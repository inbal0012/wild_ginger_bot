"""
Form Configuration Loader - Loads form definitions from various sources
Supports both Python class-based and JSON file-based configurations.
"""

import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from ..models.form_flow import (
    QuestionType, ValidationRuleType, Text, ValidationRule,
    SkipConditionItem, SkipCondition, QuestionOption, QuestionDefinition
)
from .form_config import FormConfig


class FormConfigLoader:
    """Loader for form configurations from various sources."""
    
    def __init__(self, config_source: str = "python"):
        """
        Initialize the form configuration loader.
        
        Args:
            config_source: Source type - "python" or "json"
        """
        self.config_source = config_source
        self.config_path = self._get_config_path()
        
    def _get_config_path(self) -> Optional[Path]:
        """Get the path to the configuration file."""
        if self.config_source == "json":
            # Get the directory of this file
            current_dir = Path(__file__).parent
            return current_dir / "form_config.json"
        return None
    
    def load_question_definitions(self) -> Dict[str, QuestionDefinition]:
        """Load question definitions from the configured source."""
        if self.config_source == "python":
            return self._load_from_python()
        elif self.config_source == "json":
            return self._load_from_json()
        else:
            raise ValueError(f"Unsupported config source: {self.config_source}")
    
    def load_extra_texts(self) -> Dict[str, Text]:
        """Load extra texts from the configured source."""
        if self.config_source == "python":
            return self._load_extra_texts_from_python()
        elif self.config_source == "json":
            return self._load_extra_texts_from_json()
        else:
            raise ValueError(f"Unsupported config source: {self.config_source}")
    
    def load_form_metadata(self) -> Dict[str, Any]:
        """Load form metadata from the configured source."""
        if self.config_source == "python":
            return self._load_metadata_from_python()
        elif self.config_source == "json":
            return self._load_metadata_from_json()
        else:
            raise ValueError(f"Unsupported config source: {self.config_source}")
    
    def _load_from_python(self) -> Dict[str, QuestionDefinition]:
        """Load question definitions from Python class."""
        return FormConfig.get_question_definitions()
    
    def _load_from_json(self) -> Dict[str, QuestionDefinition]:
        """Load question definitions from JSON file."""
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        questions_data = config_data.get("questions", {})
        question_definitions = {}
        
        for question_id, question_data in questions_data.items():
            question_definitions[question_id] = self._parse_question_from_json(question_data)
        
        return question_definitions
    
    def _parse_question_from_json(self, question_data: Dict[str, Any]) -> QuestionDefinition:
        """Parse a question definition from JSON data."""
        # Parse question type
        question_type_str = question_data.get("question_type", "").upper()
        question_type = QuestionType(question_type_str.lower())
        
        # Parse title
        title_data = question_data.get("title", {})
        title = Text(he=title_data.get("he", ""), en=title_data.get("en", ""))
        
        # Parse placeholder if exists
        placeholder = None
        if "placeholder" in question_data:
            placeholder_data = question_data["placeholder"]
            placeholder = Text(he=placeholder_data.get("he", ""), en=placeholder_data.get("en", ""))
        
        # Parse options if exists
        options = None
        if "options" in question_data:
            options = []
            for option_data in question_data["options"]:
                option_text_data = option_data.get("text", {})
                option_text = Text(he=option_text_data.get("he", ""), en=option_text_data.get("en", ""))
                options.append(QuestionOption(
                    value=option_data.get("value", ""),
                    text=option_text
                ))
        
        # Parse validation rules
        validation_rules = []
        for rule_data in question_data.get("validation_rules", []):
            rule_type_str = rule_data.get("rule_type", "").upper()
            rule_type = ValidationRuleType(rule_type_str.lower())
            
            error_message_data = rule_data.get("error_message", {})
            error_message = Text(he=error_message_data.get("he", ""), en=error_message_data.get("en", ""))
            
            validation_rules.append(ValidationRule(
                rule_type=rule_type,
                error_message=error_message,
                params=rule_data.get("params")
            ))
        
        # Parse skip condition if exists
        skip_condition = None
        if "skip_condition" in question_data:
            skip_data = question_data["skip_condition"]
            conditions = []
            for condition_data in skip_data.get("conditions", []):
                conditions.append(SkipConditionItem(
                    type=condition_data.get("type", ""),
                    operator=condition_data.get("operator", "equals"),
                    field=condition_data.get("field"),
                    value=condition_data.get("value")
                ))
            skip_condition = SkipCondition(
                operator=skip_data.get("operator", "OR"),
                conditions=conditions
            )
        
        return QuestionDefinition(
            question_id=question_data.get("question_id", ""),
            question_type=question_type,
            title=title,
            required=question_data.get("required", False),
            save_to=question_data.get("save_to", "Users"),
            order=question_data.get("order", 0),
            options=options,
            placeholder=placeholder,
            validation_rules=validation_rules,
            skip_condition=skip_condition
        )
    
    def _load_extra_texts_from_python(self) -> Dict[str, Text]:
        """Load extra texts from Python class."""
        return FormConfig.get_extra_texts()
    
    def _load_extra_texts_from_json(self) -> Dict[str, Text]:
        """Load extra texts from JSON file."""
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        extra_texts_data = config_data.get("extra_texts", {})
        extra_texts = {}
        
        for text_id, text_data in extra_texts_data.items():
            extra_texts[text_id] = Text(
                he=text_data.get("he", ""),
                en=text_data.get("en", "")
            )
        
        return extra_texts
    
    def _load_metadata_from_python(self) -> Dict[str, Any]:
        """Load form metadata from Python class."""
        return FormConfig.get_form_metadata()
    
    def _load_metadata_from_json(self) -> Dict[str, Any]:
        """Load form metadata from JSON file."""
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return config_data.get("form_metadata", {})
    
    def save_config_to_json(self, output_path: Optional[Path] = None) -> bool:
        """
        Save the current Python configuration to JSON format.
        Useful for creating JSON templates from Python configurations.
        """
        try:
            # Load from Python
            questions = self._load_from_python()
            extra_texts = self._load_extra_texts_from_python()
            metadata = self._load_metadata_from_python()
            
            # Convert to JSON format
            json_config = {
                "form_metadata": metadata,
                "extra_texts": {},
                "questions": {}
            }
            
            # Convert extra texts
            for text_id, text_obj in extra_texts.items():
                json_config["extra_texts"][text_id] = {
                    "he": text_obj.he,
                    "en": text_obj.en
                }
            
            # Convert questions
            for question_id, question_obj in questions.items():
                json_config["questions"][question_id] = self._question_to_json(question_obj)
            
            # Save to file
            if output_path is None:
                output_path = self.config_path or Path("form_config_export.json")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving config to JSON: {e}")
            return False
    
    def _question_to_json(self, question: QuestionDefinition) -> Dict[str, Any]:
        """Convert a QuestionDefinition to JSON format."""
        json_question = {
            "question_id": question.question_id,
            "question_type": question.question_type.value.upper(),
            "title": {
                "he": question.title.he,
                "en": question.title.en
            },
            "required": question.required,
            "save_to": question.save_to,
            "order": question.order
        }
        
        # Add placeholder if exists
        if question.placeholder:
            json_question["placeholder"] = {
                "he": question.placeholder.he,
                "en": question.placeholder.en
            }
        
        # Add options if exists
        if question.options:
            json_question["options"] = []
            for option in question.options:
                json_question["options"].append({
                    "value": option.value,
                    "text": {
                        "he": option.text.he,
                        "en": option.text.en
                    }
                })
        
        # Add validation rules
        json_question["validation_rules"] = []
        for rule in question.validation_rules:
            json_rule = {
                "rule_type": rule.rule_type.value.upper(),
                "error_message": {
                    "he": rule.error_message.he,
                    "en": rule.error_message.en
                }
            }
            if rule.params:
                json_rule["params"] = rule.params
            json_question["validation_rules"].append(json_rule)
        
        # Add skip condition if exists
        if question.skip_condition:
            json_question["skip_condition"] = {
                "operator": question.skip_condition.operator,
                "conditions": []
            }
            for condition in question.skip_condition.conditions:
                json_condition = {
                    "type": condition.type,
                    "operator": condition.operator
                }
                if condition.field:
                    json_condition["field"] = condition.field
                if condition.value is not None:
                    json_condition["value"] = condition.value
                json_question["skip_condition"]["conditions"].append(json_condition)
        
        return json_question
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the loaded configuration.
        Returns a dictionary with validation results.
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Load all configurations
            questions = self.load_question_definitions()
            extra_texts = self.load_extra_texts()
            metadata = self.load_form_metadata()
            
            # Validate questions
            if not questions:
                validation_result["errors"].append("No questions found in configuration")
                validation_result["valid"] = False
            
            # Check for duplicate question IDs
            question_ids = list(questions.keys())
            if len(question_ids) != len(set(question_ids)):
                validation_result["errors"].append("Duplicate question IDs found")
                validation_result["valid"] = False
            
            # Check for missing required fields
            for question_id, question in questions.items():
                if not question.question_id:
                    validation_result["errors"].append(f"Question {question_id}: Missing question_id")
                    validation_result["valid"] = False
                
                if not question.title.he or not question.title.en:
                    validation_result["warnings"].append(f"Question {question_id}: Missing title translations")
                
                if question.question_type in [QuestionType.SELECT, QuestionType.MULTI_SELECT, QuestionType.BOOLEAN]:
                    if not question.options:
                        validation_result["errors"].append(f"Question {question_id}: Missing options for select question")
                        validation_result["valid"] = False
            
            # Validate metadata
            if not metadata.get("form_name"):
                validation_result["warnings"].append("Missing form name in metadata")
            
            if not metadata.get("supported_languages"):
                validation_result["warnings"].append("Missing supported languages in metadata")
            
        except Exception as e:
            validation_result["errors"].append(f"Configuration validation failed: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result


# Factory function for easy configuration loading
def load_form_config(config_source: str = "python") -> FormConfigLoader:
    """
    Factory function to create a form configuration loader.
    
    Args:
        config_source: Source type - "python" or "json"
        
    Returns:
        FormConfigLoader instance
    """
    return FormConfigLoader(config_source) 