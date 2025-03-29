import json
import re
from typing import Dict, Any, List, Tuple

class ConfigHandler:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the ConfigHandler
        
        :param config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the JSON file
        
        :return: Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load configuration: {e}")
    
    def get_total_marks(self) -> float:
        """
        Get total marks for the assignment
        
        :return: Total marks as float
        """
        return float(self.config.get("Total Marks", 0))
    
    def get_marks_distribution(self) -> Dict[str, float]:
        """
        Get the marks distribution for questions
        
        :return: Dictionary mapping questions to marks
        """
        return self.config.get("Marks Distribution", {})
    
    def validate_roll_number_format(self, roll_number: str) -> bool:
        """
        Validate roll number against the submission guidelines pattern
        
        :param roll_number: Student's roll number
        :return: True if valid, False otherwise
        """
        pattern_str = self.config.get("Submission Guidelines", {}).get("File Name", "")
        if not pattern_str:
            return True  # No pattern specified, assume valid
        
        pattern = re.compile(pattern_str)
        return bool(pattern.match(roll_number))
    
    def validate_file_format(self, filename: str) -> bool:
        """
        Validate if the file has the correct format according to submission guidelines
        
        :param filename: Name of the file
        :return: True if valid, False otherwise
        """
        format_str = self.config.get("Submission Guidelines", {}).get("Format", "").lower()
        if not format_str:
            return True  # No format specified, assume valid
        
        return filename.lower().endswith(f".{format_str.lower()}")
    
    def validate_question_number(self, question: str) -> Tuple[bool, float]:
        """
        Validate if question number exists in marks distribution and return its marks
        
        :param question: Question number/identifier
        :return: Tuple of (is_valid, max_marks)
        """
        question_key = f"Question {question}"
        marks_distribution = self.get_marks_distribution()
        
        if question_key in marks_distribution:
            return True, float(marks_distribution[question_key])
        
        # Try without "Question" prefix
        if question in marks_distribution:
            return True, float(marks_distribution[question])
            
        return False, 0.0
    
    def get_assignment_name(self) -> str:
        """
        Get the assignment name
        
        :return: Assignment name
        """
        return self.config.get("Assignment Name", "Unnamed Assignment")
    
    def get_evaluator_name(self) -> str:
        """
        Get the evaluator's name
        
        :return: Evaluator's name
        """
        return self.config.get("Evaluated By", "Unknown")