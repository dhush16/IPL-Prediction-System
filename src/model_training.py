import pandas as pd
import numpy as np
import logging
import joblib
import os
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, 
                             precision_score, recall_score, f1_score, roc_auc_score)
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IPLModelTrainer:
    def __init__(self, model_dir='models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.best_model = None
        self.best_model_name = None
        self.feature_importances = None
        
    def prepare_data(self, final_df, target_col='target'):
        """Prepare data for model training."""
        logger.info("Preparing data for training...")
        
        # Separate features and target
        X = final_df.drop([target_col, 'winner', 'date', 'match_id'], axis=1, errors='ignore')
        y = final_df[target_col]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info(f"Training set: {X_train_scaled.shape}, Test set: {X_test_scaled.shape}")
        
        return X_train_scaled, X_test_scaled, y_train, y_test, X.columns
    
    def train_match_winner_model(self, final_df):
        """Train multiple match winner prediction models."""
        logger.info("=" * 60)
        logger.info("TRAINING MATCH WINNER PREDICTION MODEL")
        logger.info("=" * 60)
        
        X_train, X_test, y_train, y_test, feature_names = self.prepare_data(final_df)
        
        # Define models
        models = {
            'Random Forest': RandomForestClassifier(
                n_estimators=150, max_depth=15, random_state=42, n_jobs=-1
            ),
            'XGBoost': XGBClassifier(
                n_estimators=150, max_depth=7, learning_rate=0.1, 
                random_state=42, n_jobs=-1, eval_metric='logloss'
            ),
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=150, max_depth=7, learning_rate=0.1, random_state=42
            )
        }
        
        results = {}
        best_accuracy = 0
        
        for name, model in models.items():
            logger.info(f"\nTraining {name}...")
            model.fit(X_train, y_train)
            
            # Predictions
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
            except:
                auc = 0
            
            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train, cv=5, scoring='accuracy'
            )
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'auc': auc,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'y_pred': y_pred
            }
            
            logger.info(f"  Accuracy: {accuracy:.4f}")
            logger.info(f"  Precision: {precision:.4f}")
            logger.info(f"  Recall: {recall:.4f}")
            logger.info(f"  F1-Score: {f1:.4f}")
            logger.info(f"  AUC: {auc:.4f}")
            logger.info(f"  CV Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                self.best_model = model
                self.best_model_name = name
        
        logger.info("\n" + "=" * 60)
        logger.info(f"BEST MODEL: {self.best_model_name}")
        logger.info(f"BEST ACCURACY: {best_accuracy:.4f}")
        logger.info("=" * 60)
        
        # Feature importance
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_
            self.feature_importances = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            logger.info("\nTop 10 Feature Importances:")
            logger.info(self.feature_importances.head(10).to_string())
        
        # Confusion matrix
        cm = confusion_matrix(y_test, results[self.best_model_name]['y_pred'])
        logger.info(f"\nConfusion Matrix:\n{cm}")
        
        # Save model
        joblib.dump(self.best_model, os.path.join(self.model_dir, 'match_winner_model.pkl'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'scaler.pkl'))
        if self.feature_importances is not None:
            self.feature_importances.to_csv(
                os.path.join(self.model_dir, 'feature_importances.csv'), index=False
            )
        
        logger.info("Model saved successfully!")
        
        return self.best_model, results
    
    def train_player_performance_model(self, player_df):
        """Train player performance prediction model."""
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING PLAYER PERFORMANCE PREDICTION MODEL")
        logger.info("=" * 60)
        
        if player_df.empty or 'performance_category' not in player_df.columns:
            logger.warning("Insufficient player data for training")
            return None
        
        X = player_df.drop(['performance_category', 'player_name'], axis=1, errors='ignore')
        y = player_df['performance_category']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        model = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1)
        model.fit(X_train_scaled, y_train)
        
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        logger.info(f"Player Performance Model Accuracy: {accuracy:.4f}")
        logger.info(f"\nClassification Report:\n{classification_report(y_test, y_pred)}")
        
        # Save
        joblib.dump(model, os.path.join(self.model_dir, 'player_performance_model.pkl'))
        
        return model
    
    def predict_match(self, team1, team2, venue, toss_winner, toss_decision, team_stats):
        """Predict match winner and probability."""
        if self.best_model is None:
            logger.error("No trained model found")
            return None, 0.0
        
        # Create feature vector (this is simplified - adjust based on your actual features)
        prediction = self.best_model.predict([[1, 0, 1, 0, 0, 1, 0.5]])[0]
        probability = self.best_model.predict_proba([[1, 0, 1, 0, 0, 1, 0.5]])[0]
        
        return prediction, max(probability) * 100
    
    def save_all_models(self):
        """Save all trained models."""
        logger.info("Saving all models to disk...")
        if self.best_model is not None:
            joblib.dump(self.best_model, os.path.join(self.model_dir, 'best_model.pkl'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'scaler.pkl'))
        logger.info(f"Models saved to {self.model_dir}")


def train_all_models(matches_df, deliveries_df):
    """End-to-end training pipeline."""
    from src.feature_engineering import build_training_dataset
    
    logger.info("Starting model training pipeline...")
    
    # Build dataset
    final_df = build_training_dataset(matches_df, deliveries_df)
    
    # Initialize trainer
    trainer = IPLModelTrainer()
    
    # Train models
    trainer.train_match_winner_model(final_df)
    trainer.save_all_models()
    
    logger.info("Model training completed!")
    return trainer


if __name__ == "__main__":
    try:
        from src.data_cleaning import load_and_clean_data
        
        # Load data
        matches_df, deliveries_df = load_and_clean_data(
            'data/matches.csv',
            'data/deliveries.csv'
        )
        
        # Train models
        train_all_models(matches_df, deliveries_df)
        
    except FileNotFoundError as e:
        logger.error(f"Data files not found: {e}")
    except Exception as e:
        logger.error(f"Error in training: {e}")
