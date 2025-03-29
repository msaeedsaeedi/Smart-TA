#!/bin/bash

# Define functions
build() {
    echo "Starting build process..."
    docker build -t smart-ta .
    echo "Build completed."
}

run() {
    echo "Starting application..."
    docker run -it --rm \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/submissions:/app/submissions" \
        smart-ta
}

# Process command line arguments
process_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --build)
                BUILD=true
                shift
                ;;
            --run)
                RUN=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--build] [--run]"
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    # Initialize flags
    BUILD=false
    RUN=false

    # Process arguments
    process_args "$@"

    # Execute requested operations
    if [[ "$BUILD" == "true" ]]; then
        build
    fi

    if [[ "$RUN" == "true" ]]; then
        run
    fi

    # If no arguments provided, show usage
    if [[ "$BUILD" == "false" && "$RUN" == "false" ]]; then
        echo "Usage: $0 [--build] [--run]"
        exit 0
    fi
}

# Execute main function with all arguments
main "$@"