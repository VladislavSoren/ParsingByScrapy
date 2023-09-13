import logging

# Параметры логирования
logging.basicConfig(
    filename="py_log.log", filemode="w", format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
parsing_logger = logging.getLogger(__name__)
