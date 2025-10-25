import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report
from scripts.utils.snowflake_utils import execute_query
from scripts.utils.logger_utils import log
import argparse

# Constants
TARGET = 'IS_RETAINED_4_WEEKS'
CATEGORICAL_FEATURES = ['CREATION_APP_PLATFORM']
QUERY = """
select
    creation_app_platform,
    has_log_in_to_dashlane_f7d,
    cnt_days_log_in_to_dashlane_f7d,
    cnt_log_in_to_dashlane_events_f7d,
    has_add_new_password_to_vault_f7d,
    cnt_days_add_new_password_to_vault_f7d,
    cnt_add_new_password_to_vault_events_f7d,
    has_add_new_personal_document_to_vault_f7d,
    cnt_days_add_new_personal_document_to_vault_f7d,
    cnt_add_new_personal_document_to_vault_events_f7d,
    has_add_new_payment_method_to_vault_f7d,
    cnt_days_add_new_payment_method_to_vault_f7d,
    cnt_add_new_payment_method_to_vault_events_f7d,
    has_perform_autofill_f7d,
    cnt_days_perform_autofill_f7d,
    cnt_perform_autofill_events_f7d,
    has_generate_password_f7d,
    cnt_days_generate_password_f7d,
    cnt_generate_password_events_f7d,
    is_retained_4_weeks
from dashlane.onboarding.dim_user_early_engagement
"""
IMPACT_THRESHOLD = 1.15


def load_dataframe() -> pd.DataFrame:
    """
    Load the user early engagement data from Snowflake into a pandas DataFrame.
    """
    try:
        users_early_engagement_table = execute_query(query=QUERY, returns_results=True)
        df = pd.DataFrame.from_records(users_early_engagement_table)
    except Exception as e:
        log.error(f"Error retrieving data: {e}")
        return
    return df


def preprocess_data(X: pd.DataFrame) -> ColumnTransformer:
    """
    Preprocess the data by handling categorical and numeric features.
    """

    numeric_features = list(set(X.columns.tolist()) - set(CATEGORICAL_FEATURES))

    # One-Hot Encode the string values into new boolean columns
    # handle_unknown='ignore' prevents errors if new categories appear in test data
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    # Scale all values (critical for logistic regression)
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # apply the right transformations to the right columns
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, CATEGORICAL_FEATURES)
        ]
    )
    return preprocessor


def log_feature_coefficients(clf: Pipeline, impact_threshold: float) -> None:
    """
    Log the feature coefficients from the trained Logistic Regression model.
    """

    # Get the trained Logistic Regression model from the pipeline
    model_in_pipeline = clf.named_steps['model']

    # Get the feature names after preprocessing (this includes the new one-hot encoded columns)
    feature_names = [name.split('__', 1)[1] if '__' in name else name
                     for name in clf.named_steps['preprocessor'].get_feature_names_out()]

    # Get the coefficients
    coefficients = model_in_pipeline.coef_[0]

    # Combine into a clean DataFrame
    coef_df = pd.DataFrame({
        'Feature': feature_names,
        'Coefficient': coefficients
    })

    # Odds Ratio = exp(Coefficient)
    coef_df['Odds Ratio'] = np.exp(coef_df['Coefficient'])
    coef_df.drop(columns=['Coefficient'], axis=1, inplace=True)

    # Sort by coefficient magnitude to see the strongest drivers
    coef_df = coef_df.sort_values(by='Odds Ratio', ascending=False)

    # Filter for the most impactful (Odds Ratio significantly > 1 or < 1)
    impact_drivers = coef_df[coef_df['Odds Ratio'] >= impact_threshold]

    # log.info(impact_drivers.to_string(index=False))
    print(impact_drivers.to_string(index=False))





def main() -> None:
    """
    Main function to load data, preprocess, train logistic regression model, and log feature coefficients.
    """

    parser = argparse.ArgumentParser(
        description="Create a logistic regression model to predict user retention based on early engagement metrics.",
        epilog="Note: Options for -p, -t, --changed-files, --list-file, and --parse are available."
    )
    parser.add_argument(
        "-it",
        "--impact-threshold",
        default=IMPACT_THRESHOLD,
        type=float,
        help="Threshold for logging impactful features based on odds ratio (default: 1.15)",
    )


    args = parser.parse_args()
    impact_threshold = args.impact_threshold if args.impact_threshold else IMPACT_THRESHOLD


    df = load_dataframe()

    X = df.drop(TARGET, axis=1)
    y = df[TARGET]

    preprocessor = preprocess_data(X=X)

    model = LogisticRegression(random_state=1)

    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                        test_size=0.2,
                                                        stratify=y, # maintain class distribution
                                                        random_state=1  # use a fixed seed for reproducibility
                                                        )

    try:
        clf.fit(X_train, y_train)
    except Exception as e:
        log.error(f"Error during model fitting: {e}")
        return

    accuracy = clf.score(X_test, y_test)
    log.info(f"Model Test Accuracy: {accuracy:.2f}")

    log_feature_coefficients(clf=clf, impact_threshold=impact_threshold)


if __name__ == "__main__":
    main()
