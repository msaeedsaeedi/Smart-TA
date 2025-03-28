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
    
    # Display welcome header
    console.print(Panel.fit(
        "[bold cyan]Assignment Evaluation System[/bold cyan]",
        border_style="blue",
        padding=(1, 10)
    ))
    
    while True:
        roll_number = Prompt.ask(
            "\n[bold green]Enter roll number[/bold green]", 
            default="exit"
        )
        
        if roll_number.lower() == 'exit':
            console.print(Panel("[bold yellow]Exiting Application. Goodbye![/bold yellow]", 
                          border_style="yellow"))
            break
        
        if not evaluator.validate_roll_number(roll_number):
            console.print(f"[bold red]Invalid roll number format:[/bold red] {roll_number}")
            continue

        if not evaluator.find_student_zip(roll_number):
            console.print(f"[bold red]No submission found for roll number:[/bold red] {roll_number}")
            continue

        # Show student info panel
        console.print(Panel(
            f"[bold green]Processing submission for:[/bold green] [cyan]{roll_number}[/cyan]",
            border_style="green"
        ))
        
        while True:
            question = Prompt.ask(
                "\n[bold blue]Enter question number[/bold blue]", 
                default="back"
            )
            
            if question.lower() == 'back':
                break
            
            try:
                # Show processing message
                with console.status(f"[bold blue]Evaluating Q{question} for {roll_number}...[/bold blue]"):
                    evaluator.evaluate_submission(roll_number, question)
                
                # Success message
                console.print(Panel(
                    f"[bold green]✓[/bold green] Evaluation for [cyan]{roll_number}[/cyan] on question [cyan]{question}[/cyan] completed.",
                    border_style="green"
                ))
            except Exception as e:
                # Error message
                console.print(Panel(
                    f"[bold red]✗ Error:[/bold red] {str(e)}",
                    border_style="red"
                ))

if __name__ == "__main__":
    main()