import logging
import sys

from cavities_usage import CavitiesUsage

logger = logging.getLogger(__name__)


def green_prompt(prompt: str) -> None:
    logger.info(prompt, extra={'color': '\033[32m'})
    pass


from typing import Any


def handle_pm_input_folders(pm_input_dir, pm_input_subfolders: list[str | list[bytes]], use_cavities_dict,
                            skip_keyboard_input=False) -> tuple[list[str | list[bytes]], list[dict[str, str]]] | Any: #list[str | list[bytes]] | Any:

    # OPTION TO SKIP INTERACTIVE KEYBORD CAVITY SETTING (for example- for main post af2 pipeline stream)
    if skip_keyboard_input:
        subdir_names_to_iterate = get_from_yaml_dict(pm_input_dir, pm_input_subfolders, use_cavities_dict)
        return subdir_names_to_iterate, use_cavities_dict

    # KEYBOARD INTERACTION TO SET CUSTOM CAVITIES
    green_prompt(f"\nThe following OR subfolders are available in {pm_input_dir} directory:\n {pm_input_subfolders}")
    green_prompt("\nPlease, enter the cavities choice scenario: "
                 "\nm: manually select cavity nums for ORs "
                 "\nf: select cavities from use_cavities.yaml "
                 "\nd: Run all by default "
                 "\nx: Exit script")

    sys.stdout.flush()  #  THIS IS THE FIX
    scenario_choice = input("Please enter your choice: ")

    green_prompt(f"You have chosen: {scenario_choice}")
    if scenario_choice.strip().lower() == 'x':
        user_exit()

    elif scenario_choice.strip().lower() == 'm':
        subdir_names_to_iterate, updated_cavities_dict = set_cavities_manually(pm_input_dir, pm_input_subfolders,
                                                                               use_cavities_dict)
        return subdir_names_to_iterate, updated_cavities_dict

    elif scenario_choice.strip().lower() == 'f':
        subdir_names_to_iterate = get_from_yaml_dict(pm_input_dir, pm_input_subfolders, use_cavities_dict)
        return subdir_names_to_iterate, use_cavities_dict

    elif scenario_choice.strip().lower() == 'd':
        green_prompt(f"\nYou have chosen: {scenario_choice},"
                     f"\nall folders will be processed: {pm_input_subfolders}")
        return pm_input_subfolders, None
    else:
        logger.error(f"Unknown scenario choice: {scenario_choice}")
        logger.error(f"Exiting the script")
        sys.exit(1)


def user_exit() -> None:
    green_prompt("\nExecution cancelled by user: choice('x')")
    sys.exit(0)


def get_from_yaml_dict(pm_input_dir, pm_input_subfolders: list[str | list[bytes]], use_cavities_dict) -> list[str]:
    if use_cavities_dict is not None:
        # 1. Verify that for all keys from yaml (except "REST") correspond to existing OR_subfolders. Otherwise -exception
        pm_input_subdirs = pm_input_subfolders
        non_rest_yaml_keys = [key for item in use_cavities_dict for key in item.keys() if
                              key != "REST"]  # [item.keys()[0] for item in yaml_dict]
        missing_keys = [key for key in non_rest_yaml_keys if key not in pm_input_subdirs]
        if missing_keys:
            raise ValueError(
                f"The following yaml keys : {missing_keys} do not correspond to any {pm_input_dir} subdirectory {pm_input_subdirs}")

        # 2. Verify whether -REST: "0" is present. If yes,  all non_key directories should be skipped (continue)
        if CavitiesUsage.has_rest_zero(use_cavities_dict):
            subdir_names_to_iterate = non_rest_yaml_keys
            logger.info(f"Rest '0' found, the following subdirs are to be processed : {subdir_names_to_iterate}")
        # 3. Run over all subdirs. If subdir key is present - apply cavity mask, else is REST is present - apply rest mask, else- apply default strategy
        else:
            subdir_names_to_iterate = pm_input_subfolders
            logger.info(
                f"No Rest '0' found, all subdirs from {pm_input_dir} are to be processed : {subdir_names_to_iterate}")
    else:
        subdir_names_to_iterate = pm_input_subfolders
        logger.info(
            f"No 'use_cavities.yaml' found, all subdirs from {pm_input_dir} are to be processed : {subdir_names_to_iterate}")

    return subdir_names_to_iterate


def set_cavities_manually(
        pm_input_dir,
        pm_input_subfolders: list[str],
        use_cavities_dict
) -> tuple[list[str], list[dict[str, str]]]:
    print("\nChoose OR_name to select:")

    # # Build index → OR_NAME mapping
    # or_map: dict[int, str] = {}
    # for i, orname in enumerate(pm_input_subfolders, start=1):
    #     or_map[i] = orname
    # Build index → OR_NAME mapping
    or_map: dict[int, str] = {
        i: orname
        for i, orname
        in enumerate(pm_input_subfolders, start=1)
    }

    # Results
    manually_set_or_names: list[str] = []
    cavities_list: list[dict[str, str]] = []

    while True:  # outer loop: OR selection
        for i, orname in or_map.items():
            print(f" {i}. {orname}")

        choice = input("\nEnter the OR_name number: ").strip().lower()

        if choice == "x":
            user_exit()

        if not choice.isdigit():
            print(f"Please enter a valid number from 1 to {len(pm_input_subfolders)}")
            continue

        choice_num = int(choice)

        if choice_num not in or_map:
            print(f"Please enter a number from 1 to {len(pm_input_subfolders)}")
            continue

        selected_or = or_map[choice_num]
        print(f"\nSelected OR_NAME: {selected_or}")

        # ---- cavity input loop ----
        while True:
            cavity_numbers = input(
                "\nEnter cavity numbers (cspf, cvpl, p2rk, pupp): "
            ).strip().lower()

            if cavity_numbers == "x":
                user_exit()

            if len(cavity_numbers) != 4:
                print(
                    f"Please enter exactly 4 digits "
                    f"(you entered: {cavity_numbers})"
                )
                continue

            if not all(c in CavitiesUsage.ALLOWED_VALUES for c in cavity_numbers):
                print(
                    f"All 4 digits must be in the range 1–5 "
                    f"(you entered: {cavity_numbers})"
                )
                continue

            break

        # ---- handle overwrite or new entry ----
        existing_index = None
        for idx, entry in enumerate(cavities_list):
            if selected_or in entry:
                existing_index = idx
                break

        if existing_index is not None:
            print(
                f"Overwriting cavities for OR_NAME {selected_or}: "
                f"{cavities_list[existing_index][selected_or]} → {cavity_numbers}"
            )
            cavities_list[existing_index][selected_or] = cavity_numbers
        else:
            print(f"\nSetting OR_NAME {selected_or} to cavities {cavity_numbers}")
            cavities_list.append({selected_or: cavity_numbers})
            manually_set_or_names.append(selected_or)

        # ---- ask whether to continue ----
        next_choice = input(
            "\nWould you like to set cavities for next OR_name? (y/yes/1 to continue): "
        ).strip().lower()

        if next_choice not in {"y", "yes", '1'}:
            print("\nManual cavity selection finished by user.")
            break

    # ---- final consistency check ----
    assert len(manually_set_or_names) == len(cavities_list), (
        "Internal error: OR_NAME list and cavities list lengths do not match"
    )

    # In case of manual cavities set, the rest (non-specified)  should be ignored
    # hence adding - REST: "0" - to skip the rest
    cavities_list.append({'REST': "0"})
    return manually_set_or_names, cavities_list
