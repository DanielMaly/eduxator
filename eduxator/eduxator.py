import click
from .cli import CLI


@click.command()
@click.argument('course_identifier', required=False)
@click.argument('class_identifier', required=False)
@click.argument('classification_column', required=False)
@click.argument('student_username', required=False)
@click.argument('value_change', required=False)
@click.option('--fulltime', 'student_type', flag_value='fulltime', default=True)
@click.option('--parttime', 'student_type', flag_value='parttime')
@click.option('--cookie', default='~/.edux.cookie')
def run(course_identifier, class_identifier, classification_column, student_username,
        value_change, student_type, cookie):
    print('Course identifier is {}'.format(course_identifier))

    # First, we need to check the cookie and reprompt for it if necessary
    # Then we need to ask for any missing arguments in order to navigate to the correct shell step
    # If we have every single argument, we'll perform the action immediately and land on the final shell step.

    # I'll implement this first with dummy data and test it.
    # Once the shell is complete, we'll move on to other stuff
    CLI()


def main():
    run()