# Moodle-RAG

## Overview
Moodle-RAG is an innovative API designed to facilitate interactive chat functionalities using Large Language Models (LLMs) based on information extracted from a Moodle site. By employing Retrieval-Augmented Generation (RAG) methods, the chat feature is significantly enhanced with custom knowledge about the Moodle site, which is scraped daily. This process builds a vector database containing detailed knowledge about available courses and their contents, ensuring that the chat functionality is both informative and contextually relevant.

## Features
- **Interactive Chat**: Engage in conversations powered by LLMs.
- **Custom Knowledge Integration**: Utilizes a vector database built from Moodle site data for contextually relevant responses.
- **Daily Updates**: The knowledge database is updated daily to ensure the chat feature reflects the most current information.
- **Easy Integration**: Designed to be easily integrated with existing Moodle sites.

## Installation

### Using Docker
To get started with Docker, run:
```bash
docker compose up
```

### Manual Installation
For a manual setup, follow these steps:
```bash
pip install -r requirements.txt
uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
```

## Configuration
Before running Moodle-RAG, ensure you have set the following environment variables:

```env
HOST_PORT=
MINI_CUSTOM_LLM_URL=
DEFAULT_CUSTOM_LLM_URL=
MOODLE_URL=
MOODLE_API_TOKEN=
```

### Important Notes:
- **Moodle REST API**: Moodle-RAG utilizes Moodle's REST API for data retrieval. Ensure that the REST protocol is enabled in your Moodle site settings. Navigate to *Site administration > Plugins > Web services > Manage protocols* and enable the REST protocol.
- **API Token**: An API token is required for Moodle-RAG to authenticate with your Moodle site. Generate an API token by going to *Site administration > Plugins > Web services > Manage tokens*. Use this token for the `MOODLE_API_TOKEN` environment variable.

## Usage
After installation and configuration, Moodle-RAG can be accessed at `http://localhost:<HOST_PORT>` or the specified host and port.

## Contributing
We welcome contributions! If you're interested in helping improve Moodle-RAG, please take a look at our contributing guidelines. To get started, fork the repository and submit a pull request with your proposed changes.

## Support and Contact
If you encounter any issues or have questions, please file an issue on the GitHub repository. For more direct support, you can contact the project maintainers at [contact@example.com](mailto:contact@example.com).

## License
Moodle-RAG is released under the [MIT License](LICENSE). See the LICENSE file for more details.