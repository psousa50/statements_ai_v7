import logging
import re
from typing import Dict, List

import pandas as pd

from app.domain.dto.statement_processing import FilterCondition, FilterOperator, FilterPreview, LogicalOperator, RowFilter

logger = logging.getLogger("app")


class RowFilterService:
    """Service for applying row filters to dataframes during statement processing"""

    def apply_filters(self, df: pd.DataFrame, row_filter: RowFilter) -> pd.DataFrame:
        """Apply row filters to a DataFrame and return the filtered DataFrame"""
        if not row_filter or not row_filter.conditions:
            return df

        try:
            # Create a boolean mask for each condition
            condition_masks = []
            for condition in row_filter.conditions:
                mask = self._evaluate_condition(df, condition)
                condition_masks.append(mask)

            # Combine masks based on logical operator
            if row_filter.logical_operator == LogicalOperator.AND:
                final_mask = pd.Series([True] * len(df))
                for mask in condition_masks:
                    final_mask = final_mask & mask
            else:  # OR
                final_mask = pd.Series([False] * len(df))
                for mask in condition_masks:
                    final_mask = final_mask | mask

            # Apply the filter
            filtered_df = df[final_mask].copy()
            logger.info(f"Row filtering: {len(df)} rows -> {len(filtered_df)} rows")
            return filtered_df

        except Exception as e:
            logger.error(f"Error applying row filters: {str(e)}")
            # Return original dataframe if filtering fails
            return df

    def preview_filters(self, df: pd.DataFrame, row_filter: RowFilter) -> FilterPreview:
        """Preview the effect of row filters without applying them"""
        if not row_filter or not row_filter.conditions:
            all_indices = list(range(len(df)))
            return FilterPreview(
                total_rows=len(df),
                included_rows=len(df),
                excluded_rows=0,
                included_row_indices=all_indices,
                excluded_row_indices=[],
            )

        try:
            # Create a boolean mask for each condition
            condition_masks = []
            for condition in row_filter.conditions:
                mask = self._evaluate_condition(df, condition)
                condition_masks.append(mask)

            # Combine masks based on logical operator
            if row_filter.logical_operator == LogicalOperator.AND:
                final_mask = pd.Series([True] * len(df))
                for mask in condition_masks:
                    final_mask = final_mask & mask
            else:  # OR
                final_mask = pd.Series([False] * len(df))
                for mask in condition_masks:
                    final_mask = final_mask | mask

            # Get indices
            included_indices = df[final_mask].index.tolist()
            excluded_indices = df[~final_mask].index.tolist()

            return FilterPreview(
                total_rows=len(df),
                included_rows=len(included_indices),
                excluded_rows=len(excluded_indices),
                included_row_indices=included_indices,
                excluded_row_indices=excluded_indices,
            )

        except Exception as e:
            logger.error(f"Error previewing row filters: {str(e)}")
            # Return no filtering if preview fails
            all_indices = list(range(len(df)))
            return FilterPreview(
                total_rows=len(df),
                included_rows=len(df),
                excluded_rows=0,
                included_row_indices=all_indices,
                excluded_row_indices=[],
            )

    def _evaluate_condition(self, df: pd.DataFrame, condition: FilterCondition) -> pd.Series:
        """Evaluate a single filter condition and return a boolean mask"""
        if condition.column_name not in df.columns:
            # If column doesn't exist, return all False
            return pd.Series([False] * len(df))

        column_data = df[condition.column_name]

        # Convert to string for text operations
        if condition.operator in [
            FilterOperator.CONTAINS,
            FilterOperator.NOT_CONTAINS,
            FilterOperator.EQUALS,
            FilterOperator.NOT_EQUALS,
            FilterOperator.REGEX,
        ]:
            column_data = column_data.astype(str)
            if not condition.case_sensitive:
                column_data = column_data.str.lower()
                value = condition.value.lower() if condition.value else ""
            else:
                value = condition.value if condition.value else ""

        # Apply the condition
        if condition.operator == FilterOperator.CONTAINS:
            return column_data.str.contains(value, na=False)
        elif condition.operator == FilterOperator.NOT_CONTAINS:
            return ~column_data.str.contains(value, na=False)
        elif condition.operator == FilterOperator.EQUALS:
            return column_data == value
        elif condition.operator == FilterOperator.NOT_EQUALS:
            return column_data != value
        elif condition.operator == FilterOperator.REGEX:
            try:
                flags = 0 if condition.case_sensitive else re.IGNORECASE
                return column_data.str.contains(value, regex=True, flags=flags, na=False)
            except re.error:
                # Invalid regex, return all False
                return pd.Series([False] * len(df))
        elif condition.operator == FilterOperator.IS_EMPTY:
            return column_data.isna() | (column_data.astype(str).str.strip() == "")
        elif condition.operator == FilterOperator.IS_NOT_EMPTY:
            return ~(column_data.isna() | (column_data.astype(str).str.strip() == ""))
        elif condition.operator in [
            FilterOperator.GREATER_THAN,
            FilterOperator.LESS_THAN,
            FilterOperator.GREATER_THAN_OR_EQUAL,
            FilterOperator.LESS_THAN_OR_EQUAL,
        ]:
            # Convert to numeric for comparison
            try:
                numeric_column = pd.to_numeric(column_data, errors="coerce")
                numeric_value = float(condition.value) if condition.value else 0

                if condition.operator == FilterOperator.GREATER_THAN:
                    return numeric_column > numeric_value
                elif condition.operator == FilterOperator.LESS_THAN:
                    return numeric_column < numeric_value
                elif condition.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                    return numeric_column >= numeric_value
                elif condition.operator == FilterOperator.LESS_THAN_OR_EQUAL:
                    return numeric_column <= numeric_value
            except (ValueError, TypeError):
                # If conversion fails, return all False
                return pd.Series([False] * len(df))

        # Default: return all False
        return pd.Series([False] * len(df))

    def suggest_common_filters(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> List[FilterCondition]:
        """Suggest common filter patterns based on the data"""
        suggestions = []

        try:
            # Suggest filtering out empty amounts
            if "amount" in column_mapping and column_mapping["amount"] in df.columns:
                amount_col = column_mapping["amount"]
                empty_amounts = df[amount_col].isna().sum() + (df[amount_col].astype(str).str.strip() == "").sum()
                if empty_amounts > 0:
                    suggestions.append(
                        FilterCondition(column_name=amount_col, operator=FilterOperator.IS_NOT_EMPTY, value=None)
                    )

            # Suggest filtering out empty descriptions
            if "description" in column_mapping and column_mapping["description"] in df.columns:
                desc_col = column_mapping["description"]
                empty_descriptions = df[desc_col].isna().sum() + (df[desc_col].astype(str).str.strip() == "").sum()
                if empty_descriptions > 0:
                    suggestions.append(FilterCondition(column_name=desc_col, operator=FilterOperator.IS_NOT_EMPTY, value=None))

            # Suggest filtering out zero amounts
            if "amount" in column_mapping and column_mapping["amount"] in df.columns:
                amount_col = column_mapping["amount"]
                try:
                    numeric_amounts = pd.to_numeric(df[amount_col], errors="coerce")
                    zero_amounts = (numeric_amounts == 0).sum()
                    if zero_amounts > 0:
                        suggestions.append(
                            FilterCondition(column_name=amount_col, operator=FilterOperator.NOT_EQUALS, value="0")
                        )
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Error generating filter suggestions: {str(e)}")

        return suggestions
