class CavitiesUsage:
    # Allowed values for non-"REST" keys
    ALLOWED_VALUES = ('1', '2', '3', '4', '5')

    @classmethod
    def verify(cls, yaml_dict)->bool:
        """
        Verify the structure and values of the YAML configuration.

        Args:
            yaml_dict (list of dict): The YAML object as a list of single-key dictionaries.

        Raises:
            ValueError: If the structure or values are invalid.
        """
        # Allow empty dictionaries (e.g., empty YAML or only comments)
        if not yaml_dict:
            return True

        if not isinstance(yaml_dict, list):
            raise ValueError("Expected a list of dictionaries.")

        for item in yaml_dict:
            if not isinstance(item, dict) or len(item) != 1:
                raise ValueError(f"Each item must be a single-key dictionary: got {item}")

            key, value = next(iter(item.items()))

            # Check key type
            if not isinstance(key, str):
                raise ValueError(f"Key '{key}' is not a string.")

            # Check value type
            if not isinstance(value, str):
                raise ValueError(f"Value for key '{key}' is not a string. ({value})")

            # For "REST" key "0" value is allowed - to skip all non-specified ORs
            if key == "REST" and value == "0":
                return True

            # Check value length
            if len(value) != 4:
                raise ValueError(f"Value for key '{key}' must be 4 characters long. Got: '{value}'")

            # Check value content
            if not all(c in cls.ALLOWED_VALUES for c in value):
                raise ValueError(
                    f"Value for key '{key}' contains invalid characters: '{value}'. Allowed: {cls.ALLOWED_VALUES}.")

        return True

    from typing import List, Dict
    @classmethod
    def has_rest_zero(cls, yaml_dict: List[Dict[str, str]]) -> bool:
        return any(key == "REST" and value == "0"
                   for item in yaml_dict
                   for key, value in item.items()
                   )
    @classmethod
    def get_value_for_key(cls, yaml_dict, target_key) -> str | None:
        """
        Check if a key exists in the YAML dictionary and return its value if found.

        Args:
            yaml_dict (list[dict[str, str]]): The YAML object as a list of single-key dictionaries.
            target_key (str): The key to search for.

        Returns:
            str: The value associated with the key, or None if the key is not found.
        """
        for item in yaml_dict:
            if target_key in item:
                return item[target_key]
        return None  # Key not found
