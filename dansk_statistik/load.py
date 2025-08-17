from api import fetch_statbank_data

#FOLK1C: Population at the first day of the quarter by region, sex, ancestry and country of origin
def load_FOLK1C(current_year: int):
    return fetch_statbank_data(
        table_id="FOLK1C",
        variables={
            "OMRÅDE": ["000"],
            "IELAND": ["*"],              
            "HERKOMST": ["5","4","3"],
            "KØN": ["TOT"],                 
            "ALDER": ["20-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95-99", "100OV"],              
            "TID": [f"{y}K4" for y in range(2015, current_year )] 
        }
    )

load_FOLK1C(2023)

#INDKP109: Income for people by region, sex, age, ancestry and type of income
def load_INDKP109(current_year: int):
    return fetch_statbank_data(
        table_id="INDKP109",
        variables={
            "ALDER1": ["TOT"],
            "REGLAND": ["000"],
            "KOEN": ["MOK"],
            "HERKOMST": ["DANSK", "IND_VEST", "IND_ANDRE"],  
            "INDKOMSTTYPE": [ "105"], #Taxable income
            "ENHED": ["121"],  # DKK per person 
            "tid": [str(y) for y in range(2015, current_year)]
        }
    )



def load_INDKP109_totals(current_year:int):
    return fetch_statbank_data(
        table_id="INDKP109",
        variables={
            "ALDER1": ["TOT"],
            "REGLAND": ["000"],
            "KOEN": ["MOK"],
            "HERKOMST": ["DANSK", "IND_VEST", "IND_ANDRE"],
            "INDKOMSTTYPE": ["105"],  # taxable income (suma)
            "ENHED": ["110"],         # tys. DKK
            "TID": [str(y) for y in range(2015, current_year+1)]
        }
    )
