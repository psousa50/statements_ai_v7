import re
from datetime import datetime

import pandas as pd
import json
import logging

logger_content = logging.getLogger("app.llm.big")
logger = logging.getLogger("app")


class TransactionNormalizer:
    def normalize(self, df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
        result_df = pd.DataFrame()

        # Validate the column mapping
        if not column_mapping:
            raise ValueError("Column mapping is empty")
            
        # Clean up empty strings in the mapping
        cleaned_mapping = {}
        for key, value in column_mapping.items():
            if value and value.strip() != "":
                cleaned_mapping[key] = value
        
        # Log the cleaned mapping
        logger.debug(f"Original mapping: {column_mapping}")
        logger.debug(f"Cleaned mapping: {cleaned_mapping}")
        
        # Check if we have the traditional amount field or debit/credit fields
        has_amount = "amount" in cleaned_mapping and cleaned_mapping["amount"]
        has_debit_credit = ("debit_amount" in cleaned_mapping and cleaned_mapping["debit_amount"] and
                          "credit_amount" in cleaned_mapping and cleaned_mapping["credit_amount"])
        
        # Determine which schema we're using
        if has_amount:
            logger.info("Using single amount field schema")
            required_keys = ["date", "amount", "description"]
        elif has_debit_credit:
            logger.info("Using debit/credit amount fields schema")
            required_keys = ["date", "debit_amount", "credit_amount", "description"]
        else:
            # Default to standard schema with just date and description
            logger.info("No valid amount fields found, using minimal schema")
            required_keys = ["date", "description"]
            
        # Update column_mapping to use the cleaned version
        column_mapping = cleaned_mapping
        
        # Check required keys exist in the mapping
        missing_keys = [key for key in required_keys if key not in column_mapping]
        if missing_keys:
            raise ValueError(f"Missing required keys in column mapping: {', '.join(missing_keys)}")
            
        # Get column names from mapping
        date_col = column_mapping["date"]
        description_col = column_mapping["description"]
        
        # Handle amount fields based on schema
        if has_amount:
            amount_col = column_mapping["amount"]
        elif has_debit_credit:
            debit_col = column_mapping["debit_amount"]
            credit_col = column_mapping["credit_amount"]
        else:
            # Default to amount for backward compatibility
            amount_col = column_mapping.get("amount", "")
        
        # Validate that mapped columns are not empty
        empty_columns = []
        for col_name, mapped_col in column_mapping.items():
            if col_name in required_keys and (not mapped_col or mapped_col.strip() == ""):
                empty_columns.append(col_name)
        
        if empty_columns:
            raise ValueError(f"Empty column mappings for: {', '.join(empty_columns)}")
        
        # Check if the mapped columns exist in the DataFrame
        missing_columns = []
        for col_name, mapped_col in column_mapping.items():
            if mapped_col not in df.columns:
                missing_columns.append(mapped_col)
        
        # If there are missing columns, try to use positional mapping
        if missing_columns:
            logger.warning(f"Missing mapped columns in DataFrame: {', '.join(missing_columns)}")
            logger.warning(f"Attempting to use positional mapping instead")
            
            # Get the number of columns in the DataFrame
            num_cols = len(df.columns)
            
            # Create a positional mapping based on expected column order: date, amount, description
            positional_mapping = {}
            
            # Map date to first column if available
            if num_cols > 0:
                positional_mapping["date"] = df.columns[0]
                logger.info(f"Mapping 'date' to column {df.columns[0]}")
            
            # Map amount to second column if available
            if num_cols > 1:
                positional_mapping["amount"] = df.columns[1]
                logger.info(f"Mapping 'amount' to column {df.columns[1]}")
            
            # Map description to third column if available
            if num_cols > 2:
                positional_mapping["description"] = df.columns[2]
                logger.info(f"Mapping 'description' to column {df.columns[2]}")
            
            # Check if we have all required mappings
            if len(positional_mapping) < 3:
                raise ValueError(f"Not enough columns in DataFrame for positional mapping. Found {num_cols} columns, need at least 3.")
            
            # Update the column mapping with positional mapping
            date_col = positional_mapping["date"]
            amount_col = positional_mapping["amount"]
            description_col = positional_mapping["description"]
            
            logger.info(f"Using positional mapping: date={date_col}, amount={amount_col}, description={description_col}")
        
            
        # Log the DataFrame columns for debugging
        logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        logger.debug(f"Mapped columns: date={date_col}, amount={amount_col}, description={description_col}")
        logger.debug(f"DataFrame shape: {df.shape}")
        logger.debug(f"DataFrame head:\n{df.head()}")
        
        # If the DataFrame is empty, return an empty result
        if df.empty:
            logger.warning("Empty DataFrame provided to normalizer")
            return result_df
        
        logger.debug(f"Date column: {date_col}")
        logger.debug(f"Description column: {description_col}")
        logger.debug(f"DataFrame columns: {df.columns.tolist()}")
        logger.debug(f"DataFrame shape: {df.shape}")

        # Process date column
        result_df["date"] = self._normalize_dates(df[date_col])
        
        # Process amount column(s)
        if has_amount:
            logger.debug(f"Amount column: {amount_col}")
            result_df["amount"] = self._normalize_amounts(df[amount_col])
        elif has_debit_credit:
            logger.debug(f"Debit column: {debit_col}, Credit column: {credit_col}")
            # Process debit and credit columns and combine them into a single amount column
            # Debit is negative, credit is positive
            debit_amounts = self._normalize_amounts(df[debit_col])
            credit_amounts = self._normalize_amounts(df[credit_col])
            
            # Convert NaN to 0
            debit_amounts = debit_amounts.fillna(0)
            credit_amounts = credit_amounts.fillna(0)
            
            # Combine: debit is negative, credit is positive
            result_df["amount"] = credit_amounts.subtract(debit_amounts)
        else:
            # Try to infer amount from column names if no explicit mapping
            amount_columns = [col for col in df.columns if 'amount' in str(col).lower()]
            debit_columns = [col for col in df.columns if 'debit' in str(col).lower() or 'paid' in str(col).lower() or 'payment' in str(col).lower()]
            credit_columns = [col for col in df.columns if 'credit' in str(col).lower() or 'received' in str(col).lower() or 'income' in str(col).lower()]
            
            if amount_columns:
                logger.info(f"Found potential amount column: {amount_columns[0]}")
                result_df["amount"] = self._normalize_amounts(df[amount_columns[0]])
            elif debit_columns and credit_columns:
                logger.info(f"Found potential debit column: {debit_columns[0]} and credit column: {credit_columns[0]}")
                debit_amounts = self._normalize_amounts(df[debit_columns[0]]).fillna(0)
                credit_amounts = self._normalize_amounts(df[credit_columns[0]]).fillna(0)
                result_df["amount"] = credit_amounts.subtract(debit_amounts)
            else:
                # Fallback to positional mapping if needed
                logger.warning("No valid amount columns found, using default amount")
                result_df["amount"] = 0.0
        
        # Process description column
        # Handle NaN values in description field
        descriptions = df[description_col]
        result_df["description"] = descriptions.fillna("").astype(str)

        # Convert pandas Timestamp objects to string format for JSON serialization
        if "date" in result_df.columns:
            result_df["date"] = result_df["date"].apply(lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else x)

        return result_df

    def _normalize_dates(self, date_series):
        normalized_dates = []

        for date_val in date_series:
            # Check if the value is already a datetime object
            if isinstance(date_val, (datetime, pd.Timestamp)):
                logger.debug(f"Already a datetime object: {date_val}")
                normalized_dates.append(date_val)
                continue
                
            # Handle string dates
            try:
                # Convert to string if it's not already
                date_str = str(date_val) if date_val is not None else ""
                
                if not date_str or date_str.lower() == 'nan':
                    logger.debug("Empty or NaN date value")
                    normalized_dates.append(None)
                    continue
                    
                # Try common date formats
                date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y"]
                for fmt in date_formats:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # If none of the formats match, try pandas to_datetime
                    try:
                        date_obj = pd.to_datetime(date_str)
                    except Exception as e:
                        logger.debug(f"Failed to parse date '{date_str}': {str(e)}")
                        date_obj = None
                        
                normalized_dates.append(date_obj)
            except Exception as e:
                logger.warning(f"Error processing date value '{date_val}': {str(e)}")
                normalized_dates.append(None)

        return normalized_dates

    def _normalize_amounts(self, amount_series):
        normalized_amounts = []

        for amount_val in amount_series:
            if isinstance(amount_val, (int, float)):
                normalized_amounts.append(float(amount_val))
                continue

            amount_str = str(amount_val)

            if "," in amount_str and "." in amount_str:
                if amount_str.find(",") > amount_str.find("."):
                    amount_str = amount_str.replace(".", "").replace(",", ".")
                else:
                    amount_str = amount_str.replace(",", "")
            elif "," in amount_str:
                amount_str = amount_str.replace(",", ".")

            amount_str = re.sub(r"[^\d.-]", "", amount_str)

            try:
                amount = float(amount_str)
                normalized_amounts.append(amount)
            except ValueError:
                logger.debug("Invalid amount: %s", amount_str)
                normalized_amounts.append(None)

        return normalized_amounts
