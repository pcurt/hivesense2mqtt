"""Console script for hivesense2mqtt."""

# Standard lib imports
import sys
import time

# Third-party lib imports
import click
from loguru import logger

from hivesense2mqtt.app.app import HiveSense2Mqtt


# Define this function as a the main command entrypoint
@click.command()
# Create an argument that expects an integer, and has a default value
@click.option(
    "-n",
    "--iterations",
    help="Number of times to display the sample text",
    type=int,
    default=1,
)
@click.option(
    "-v",
    "--verbose",
    help="Verbose mode",
    count=True,
)
# Get the version of the package
@click.version_option()
# Display some help
@click.help_option("-h", "--help")
def main(
    iterations: int,
    verbose: int,
) -> None:
    """Console script for hivesense2mqtt."""
    # Set the log level if required
    if verbose == 0:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    handler = HiveSense2Mqtt()
    handler.loop_start()
    try:
        while True:
            # Main loop is doing nothing
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    sys.exit(main())
