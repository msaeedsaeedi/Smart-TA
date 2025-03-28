# Smart TA

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/msaeedsaeedi/smart-ta/blob/main/requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Tired of manually compiling and running student code? The **Assignment Evaluation System** is a command-line tool designed to streamline the evaluation of C/C++ programming assignments. It offers a secure and efficient way to process submissions, execute code in isolated environments, and generate comprehensive evaluation reports.

## Key Features

* **Effortless Submission Handling:** Automatically extracts and prepares student submissions from ZIP files.
* **Secure Sandboxed Execution:** Runs student code in isolated environments, preventing any unintended interference with your system.
* **Interactive Evaluation:** Supports programs requiring user input through a pseudo-terminal interface.
* **Detailed Insights:** Generates structured JSON logs for each evaluation, providing a clear record of the execution process.
* **User-Friendly Interface:** Presents a clean and formatted terminal interface powered by the `rich` library.

## Prerequisites

Before you begin, ensure you have the following installed:

* **Python:** Version 3.6 or higher.
* **Rich:** A Python library for rich text and beautiful formatting in the terminal. You can install it using `pip install rich`.
* **G++ Compiler:** The GNU C++ compiler, necessary for compiling C/C++ submissions.

## Installation

Get up and running in just a few steps:

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/msaeedsaeedi/smart-ta.git](https://github.com/msaeedsaeedi/smart-ta.git)
    cd smart-ta
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Quick Start

Simply run the bootstrap script to start the evaluation process:

```bash
./bootstrap.sh
```

This will launch the application and guide you through the evaluation workflow.

## Contributing

We welcome contributions to make this system even better! If you have suggestions, bug reports, or would like to add new features, please feel free to:

1.  Fork the repository.
2.  Create a new branch for your feature or fix.
3.  Make your changes and commit them.
4.  Push your changes to your fork.
5.  Submit a pull request.

Please ensure your code adheres to the project's coding standards.

## License

This project is licensed under the [MIT License](LICENSE).