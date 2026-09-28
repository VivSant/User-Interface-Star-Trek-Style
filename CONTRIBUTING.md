Automated Formatting & Static Analysis (PEP 8)
To eliminate stylistic bikeshedding and ensure strict PEP 8 compliance, we have abstracted all code formatting and linting to Black and Ruff. This deterministic pipeline is enforced locally via pre-commit hooks, guaranteeing that no poorly formatted code enters the version control history. All contributors must execute pre-commit install in their local environment before staging their first commit.

Interface & Logic Documentation
For optimal codebase maintainability and to support future automated documentation generation, we are standardizing on Google-style docstrings. Every class and function, especially custom UI widgets and state altering methods, must include a concise behavioral summary, explicitly defined paramters under an Args: block and expected outputs under a Returns: block

Lexical Naming Conventions
Given the heavy modularity required for a custom graphical interface, strict namespace rules are critical for readability and separating logic from presentation:

    Class Definitions:
    Strictly PascalCase (e.g., class NavigationDisplay:)

    Functions, Methods, & Variables:
    Strictly snake_case (e.g., def draw_square_button(): or current_screen_height = 1080)

    Global constants:
    Strictly UPPER_SNAKE_CASE (e.g., OKUDA_ORANGE = "#FF9900")



This was built by referencing the Pandas library documentation.
Find it here: https://pandas.pydata.org/docs/dev/development/contributing_codebase.html
