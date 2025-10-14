import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

loggerWhappi = logging.getLogger("Whappi")
loggerCloudVision = logging.getLogger("CloudVision")
loggerGSpreadsheet = logging.getLogger("GSpreadsheet")
loggerOpenAI = logging.getLogger("OpenAI")
