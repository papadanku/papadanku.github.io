
# Contributing to ReadShade

First, thank you for considering contributing to ReadShade! We appreciate you taking the time to help improve this documentation project.

ReadShade is designed to be a simple and unbiased platform for sharing knowledge. We want to make it as easy as possible for anyone to contribute, regardless of their technical background.

## How You Can Contribute

There are many ways you can help, from fixing typos to writing entire new guides.

### Getting Started

To start contributing, you only need a few things on your computer:

1. **Python**: The programming language we use.
2. **Sphinx**: The tool that builds our documentation site.
3. **A Text Editor**: Any text editor like VS Code, Notepad++, or Sublime Text will work.

You can set up your local environment by following these steps:

1. **Fork the repository**: Click the "Fork" button at the top-right of the repository page on GitHub. This creates your own copy of the project.
2. **Clone your fork**: Copy your fork to your local machine using Git:

    ```bash
    git clone https://github.com/YOUR-USERNAME/ReadShade.git
    cd ReadShade
    ```

3. **Install the requirements**: Install the necessary Python packages.

    ```bash
    pip install -r requirements.txt
    ```

### Making Changes

Now you are ready to make changes!

1. **Find the file**: All of our documentation lives in the `source/` directory. Find the `.rst` file you want to edit or create a new one in the appropriate folder.
2. **Edit the content**: Our documentation is written in reStructuredText (`.rst`). You can learn the basics, but for most changes, you can simply copy the style you see in other files.
3. **Preview your changes**: Before you submit your changes, build the site locally to see how it looks. Run this command from the root folder of the project:

    ```bash
    sphinx-build -b html . _build
    ```

    After it finishes, open the `_build/index.html` file in your web browser to see your changes.

### Submitting Your Changes

Once you are happy with your changes, it's time to submit them.

1. **Commit your changes**: Save your changes in Git with a clear message about what you did.

    ```bash
    git add .
    git commit -m "feat: Add a new guide for X"
    ```

2. **Push your changes**: Send your committed changes to your fork on GitHub.

    ```bash
    git push origin main
    ```

3. **Create a Pull Request**: Go to your fork on GitHub and click the "New pull request" button. Our team will review your changes, provide feedback if needed, and merge them.

## Writing Style

To keep our documentation consistent and easy to read, please follow these guidelines:

- **Write in plain English**: Use simple and clear language.
- **Use active voice**: Write direct and engaging content. For example, instead of "The button can be clicked," write "Click the button."
- **AI-Assisted Content**: We use AI tools like Google's Gemini CLI to help create and revise content. We encourage you to use them as well to help with grammar and clarity.

## Code of Conduct

We want our community to be a friendly and welcoming place. Please be respectful and considerate in all your interactions. We value every contribution and appreciate your effort to help us build a great resource for everyone.
