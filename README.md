# 📝 Message Queue Consumer for E-mail Delivery

This project implements a message queue consumer application that processes notification delivery tasks via email.

## 📋 Prerequisites

- **Python 3+**: Ensure you have Python 3 installed. You can download it from [python.org](https://www.python.org/downloads/).
- **Docker and Docker Compose**: Install Docker and Docker Compose from [docker.com](https://www.docker.com/).
- **SMTP Server**: A valid SMTP server is required for email delivery.

## 🚀 Usage

### 🐍 Python

1. **Create a virtual environment and activate it**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   # For Windows, use:
   # source venv/Scripts/activate
   ```

2. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env.secrets` file** with the following content:

   ```bash
   SMTP_PASSWORD='change-me'
   ```

   Refer to the [.env.secrets.example](.env.secrets.example) file for more details on configuration.

4. **Run the application**:

   ```bash
   python worker.py
   ```

5. **In another terminal, run the producer**:

   ```bash
   python producer.py
   ```

### 🐳 Docker

To deploy the RabbitMQ back-end service using Docker Compose, run:

```bash
docker compose up rabbitmq -d
```

You can access RabbitMQ in your browser at: [http://localhost:5000](http://localhost:5000).

To build and run the application in a Docker environment, use the following command:

```bash
docker compose up -d
```

If you are using Visual Studio Code, you can debug the application by pressing F5.

## 🔧 Configuration

You can configure the application by modifying the files in the `src/templates` directory and the `src/config.py` file.

The configuration YAML files handle parameters to overwrite HTML templates. You can add and model new templates to send emails along with the parameters.

## 📝 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- [Hilton Almeida](https://github.com/hiltonmbr)
- [Aléssio Almeida](https://github.com/alessioalmeida)
