from typing import List

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from scripts.utils.snowflake_utils import execute_query
from scripts.utils.logger_utils import log
import argparse
import sys

# Constants
TARGET = 'IS_RETAINED_4_WEEKS'
CATEGORICAL_FEATURES = ['CREATION_APP_PLATFORM']
NUMERIC_FEATURES = [
    'HAS_LOG_IN_TO_DASHLANE_F7D',
    'CNT_DAYS_LOG_IN_TO_DASHLANE_F7D',
    'CNT_LOG_IN_TO_DASHLANE_EVENTS_F7D',
    'HAS_ADD_NEW_PASSWORD_TO_VAULT_F7D',
    'CNT_DAYS_ADD_NEW_PASSWORD_TO_VAULT_F7D',
    'CNT_ADD_NEW_PASSWORD_TO_VAULT_EVENTS_F7D',
    'HAS_ADD_NEW_PERSONAL_DOCUMENT_TO_VAULT_F7D',
    'CNT_DAYS_ADD_NEW_PERSONAL_DOCUMENT_TO_VAULT_F7D',
    'CNT_ADD_NEW_PERSONAL_DOCUMENT_TO_VAULT_EVENTS_F7D',
    'HAS_ADD_NEW_PAYMENT_METHOD_TO_VAULT_F7D',
    'CNT_DAYS_ADD_NEW_PAYMENT_METHOD_TO_VAULT_F7D',
    'CNT_ADD_NEW_PAYMENT_METHOD_TO_VAULT_EVENTS_F7D',
    'HAS_PERFORM_AUTOFILL_F7D',
    'CNT_DAYS_PERFORM_AUTOFILL_F7D',
    'CNT_PERFORM_AUTOFILL_EVENTS_F7D',
    'HAS_GENERATE_PASSWORD_F7D',
    'CNT_DAYS_GENERATE_PASSWORD_F7D',
    'CNT_GENERATE_PASSWORD_EVENTS_F7D',
]
QUERY = f"""
SELECT
    {TARGET},
    {", ".join(CATEGORICAL_FEATURES)},
    {", ".join(NUMERIC_FEATURES)}
FROM dashlane.onboarding.dim_user_early_engagement
"""
DEFAULT_IMPACT_THRESHOLD = 1.2
RANDOM_STATE = 1


def load_dataframe() -> pd.DataFrame:
    """
    Load the user early engagement data from Snowflake into a pandas DataFrame.
    """
    try:
        users_early_engagement_table = execute_query(query=QUERY)
        df = pd.DataFrame.from_records(users_early_engagement_table)
        log.info(f"Successfully loaded {len(df)} records.")
        return df

    except Exception as e:
        log.error(f"Error retrieving or processing data: {e}")
        sys.exit(1)  # Exit if data loading fails


def build_pipeline(numeric_features: List[str], categorical_features: List[str]) -> Pipeline:
    """
    Create the full preprocessing and modeling pipeline.
    """
    # Define transformer for categorical features
    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    # Define transformer for numeric features
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    # Create the column preprocessor
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ],
    )

    # Create the full pipeline with model
    clf = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', LogisticRegression(random_state=RANDOM_STATE)) # For reproducibility
    ])
    return clf


def evaluate_model(clf: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> None:
    """
    Evaluate the trained model and log key metrics.
    """
    log.info("Evaluating model on test set...")

    # Get predictions
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Log metrics
    log.info(f"Model Test Accuracy: {accuracy:.4f}")


def log_feature_coefficients(clf: Pipeline, impact_threshold: float) -> None:
    """
    Log the feature coefficients (as odds ratios) from the logistic regression model.
    """
    log.info("Extracting feature coefficients...")
    try:
        model = clf.named_steps['model']
        preprocessor = clf.named_steps['preprocessor']

        feature_names = preprocessor.get_feature_names_out()
        # Clean up feature names for readability
        feature_names = [name.split('__')[-1] for name in feature_names]

        coefficients = model.coef_[0]

        # Odds Ratio: odds of the outcome change for a one-unit increase in the feature variable
        coef_df = pd.DataFrame({
            'Feature': feature_names,
            'Odds Ratio': np.exp(coefficients)
        })

        # Sort by magnitude
        coef_df = coef_df.sort_values(by='Odds Ratio', ascending=False)

        # Filter for impactful drivers
        impact_drivers = coef_df[
            (coef_df['Odds Ratio'] >= impact_threshold) |
            (coef_df['Odds Ratio'] <= 1 / impact_threshold)
            ]

        log.info(f"Impactful Features (Threshold: {impact_threshold})")
        log.info(f"\n{impact_drivers.to_string(index=False)}")

    except Exception as e:
        log.warning(f"Could not extract feature coefficients: {e}")


# --- Main Execution ---

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Train a logistic regression model for user retention."
    )
    parser.add_argument(
        "-it",
        "--impact-threshold",
        default=DEFAULT_IMPACT_THRESHOLD,
        type=float,
        help=f"Odds ratio threshold for logging features (default: {DEFAULT_IMPACT_THRESHOLD})",
    )
    return parser.parse_args()


def main() -> None:
    """
    Main function to run the model training and evaluation pipeline.
    """
    args = parse_args()

    df = load_dataframe()
    if df is None or df.empty:
        log.error("No data loaded. Exiting.")
        return

    X = df.drop(TARGET, axis=1)
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        stratify=y,  # Maintain class distribution
        random_state=RANDOM_STATE # For reproducibility
    )
    log.info(f"Data split: {len(X_train)} train samples, {len(X_test)} test samples.")

    clf = build_pipeline(
        numeric_features=NUMERIC_FEATURES,
        categorical_features=CATEGORICAL_FEATURES
    )

    try:
        clf.fit(X_train, y_train)
        log.info("Model training complete.")
    except Exception as e:
        log.error(f"Error during model fitting: {e}")
        return

    evaluate_model(clf, X_test, y_test)

    log_feature_coefficients(clf, impact_threshold=args.impact_threshold)


if __name__ == "__main__":
    main()
