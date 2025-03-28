import os

def find_student_zip(submissions_path: str, roll_number: str) -> str:
    """
    Find a student's submission zip file
    
    :param submissions_path: Path to submissions directory
    :param roll_number: Student's roll number
    :return: Path to zip file or None if not found
    """
    for file in os.listdir(submissions_path):
        if roll_number in file and file.endswith('.zip'):
            return os.path.join(submissions_path, file)
    return None
