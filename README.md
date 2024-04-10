# RabbitMQ Pub-Sub

This project provides a simple implementation of the publish-subscribe pattern using RabbitMQ, making it easy to set up communication between different parts of your application.

## Prerequisites

Ensure you have the following installed before proceeding:

- RabbitMQ server
- Python 3

## Installation

1. Install the required Python dependencies:

   ```bash
   pip install .
   ```

## Usage

While this project was initially standalone, it is now integrated into a larger project. For practical usage, we recommend utilizing the `mrkutil` library, which includes implemented methods for this library. Check out the [mrkutil GitHub repository](https://github.com/ivke-99/mrkutil/) for more details and examples. However, feel free to adapt this library for your own needs.

## Authors

- [@nmrkic](https://github.com/nmrkic)

## Deployment to PyPI

To deploy this package to PyPI, use the following commands:

```bash
flit build
flit publish
```

## Contributing

Contributions are always welcome! If you have any suggestions or improvements, feel free to submit a pull request or open an issue.
