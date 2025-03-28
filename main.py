from evaluator import AssignmentEvaluator
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint
from rich.style import Style
from rich.text import Text

def main():
    """
    Main entry point for the application
    """
    submissions_path = "./submissions"
    output_log_path = "./logs"
    
    # Initialize the evaluator and rich console
    evaluator = AssignmentEvaluator(submissions_path, output_log_path)
    console = Console()
    
    while True:
        console.clear()
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
                default="back"
            )
            
            if question.lower() == 'back':
                break
            
            try:
                evaluator.evaluate_submission(roll_number, question)
            except Exception as e:
                console.print(Panel(
                    f"[bold red]✗ Error:[/bold red] {str(e)}",
                    border_style="red"
                ))
            console.line(1)

if __name__ == "__main__":
    main()