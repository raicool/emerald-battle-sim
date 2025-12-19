from pygdbmi.gdbcontroller import GdbController

import log

def write_command(debugger: GdbController, msg: str, timeout: int = 5):
	response = debugger.write(msg, timeout, raise_error_on_timeout=False)
	
	log_string: str = str()
	
	log.debug(msg)
	
	for i in response:
		if (i["type"] == "output"):
			log_string += "\n" + str(i["payload"])
			
	log.debug(log_string)
	return response