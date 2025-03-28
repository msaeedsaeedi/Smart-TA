
from evaluator import AssignmentEvaluator

def main():
    """
    Main entry point for the application
    """
    submissions_path = "./submissions"
    output_log_path = "./logs"
    
    # Initialize the evaluator
    evaluator = AssignmentEvaluator(submissions_path, output_log_path)
    
    while True:
        roll_number = input("Enter roll number (or 'exit' to quit): ")
        if roll_number.lower() == 'exit':
            break
        
        if not evaluator.validate_roll_number(roll_number):
            print(f"Invalid roll number format: {roll_number}")
            continue

        if not evaluator.find_student_zip(roll_number):
            print(f"No submission found for roll number: {roll_number}")
            continue

        while True:
            question = input("Enter question number (or 'back' to go back): ")
            if question.lower() == 'back':
                break
            
            try:
                evaluator.evaluate_submission(roll_number, question)
                print(f"Evaluation for {roll_number} on question {question} completed.")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()