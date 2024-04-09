from typing import Dict, List
from pydantic import BaseModel, field_validator
from aind_data_schema.models.modalities import Modality


class DynamicModel(BaseModel):
    modalities: Dict[str, List[str]]

    @field_validator("modalities")
    def verify_valid_modality(cls, data: Dict[str, List[str]]) -> Dict[str, List[str]]:
        for key in data.keys():
            if key.lower() not in Modality._abbreviation_map: 
                raise ValueError(f"{key} not in accepted modalities")
        return data

# Example dictionary with changing key names
input_data = {
    'modalities': {
        'BEHAVIOR': [
            'file1.txt', 
            'file2.txt'
            ],
        'OPHYS': [
            'file1.txt', 
            'file2.txt'
            ]
        }
}

# Creating an instance of the DynamicModel with the input data
model_instance = DynamicModel(**input_data)

# Accessing the data
print(model_instance.modalities)