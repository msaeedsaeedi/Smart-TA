from evaluator import AssignmentEvaluator
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

def main():
    """
    Main entry point for the application
    """
    submissions_path = "./submissions"
    output_log_path = "./logs"
    
    # Initialize the evaluator and rich console
    evaluator = AssignmentEvaluator(submissions_path, output_log_path)
    console = Console()
    console.clear()
    
    while True:
        roll_number = Prompt.ask(
            "\n[bold green]Enter roll number[/bold green]", 
            default="exit"
        )
        
        if roll_number.lower() == 'exit':
            break
        
        if not evaluator.validate_roll_number(roll_number):
            console.print(f"[bold red]Invalid roll number format:[/bold red] {roll_number}")
            continue

        if not evaluator.find_student_zip(roll_number):
            console.print(f"[bold red]No submission found for roll number:[/bold red] {roll_number}")
            continue
        
        while True:
            question = Prompt.ask(
                "[bold green]Enter question number[/bold green]", 
                default="0",
            )
            
            if question.lower() == '-1':
                break
            
            if question.lower() == '0':
                evaluator.evaluate_submission(roll_number)
                break
            
            try:
                evaluator.evaluate_submission(roll_number, question)
                console.clear()
            except Exception as e:
                console.print(Panel(
                    f"[bold red]✗ Error:[/bold red] {str(e)}",
                    border_style="red"
                ))
            console.line(1)

if __name__ == "__main__":
    main()