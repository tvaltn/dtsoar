

class Data_Processor:

    # Simple method for now, just interpreting data if its 0
    def interpret_event_data(self, data):
        print("[DATA PROCESSOR] Interpreting Event Data")
        
        interpreted_data = []
        for info in data:
            for ip, value in info.items():
                if value == "0":
                    new_value = "No Value"
                    interpreted_data.append({ip:new_value})
        
        return interpreted_data
    
