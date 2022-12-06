"""Filter typosquatting-related lists.

A module that contains all functions that filter data related to typosquatting
data.
"""

import jellyfish
import Levenshtein
from mrs_spellings import MrsWord
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import re

import constants

MAX_DISTANCE = constants.MAX_DISTANCE
MIN_LEN_PACKAGE_NAME = constants.MIN_LEN_PACKAGE_NAME


def filter_by_package_name_len(package_list, min_len=MIN_LEN_PACKAGE_NAME):
    """Keep packages whose name is >= a minimum length.

    Args:
        package_list (list): a list of package names
        min_len (int): a minimum length of charactersArgs

    Returns:
        list: filtered package names
    """
    return [pkg for pkg in package_list if len(pkg) >= min_len]


def __get_threshold_edit_distance(word_length):
    return 1
    if word_length <= 5:
        return 1
    if word_length <= 10:
        return 2
    if word_length <= 15:
        return 3
    return 4


def misinfo_name(package_name):
    if ("python" in package_name):
        words = package_name.replace("python", "py")

    elif ("py" in package_name) and ("python" not in package_name):
        words = package_name.replace("py", "python")

    else:
        words = None

    return words


def get_misinfo_close_names(package_of_interest, all_packages):
    """Find packages that are close to the misinformaed package (py<->python).

    """
    candidate = misinfo_name(package_name=package_of_interest)

    result = list()
    if candidate and candidate in all_packages:
        result.append(candidate)
    return result


def get_qwerty_close_package_names(package_of_interest, all_packages):
    """Find packages that are close to the given package on QWERTY keyboard.

    Note that this check might catch some packages not caught by Levenshtein distance
    method.

    """
    candidates = MrsWord(package_of_interest).qwerty_swap()
    candidates = set(" ".join(candidates).split(" "))
    result = list(candidates.intersection(set(all_packages)))
    return result


def get_leetspeak_package_names(package_of_interest, all_packages):
    mp = dict()
    mp["o"] = "0"
    mp["O"] = "0"
    mp["l"] = "1"
    mp["s"] = "5"
    mp["S"] = "5"
    candidates = list()
    for k, v in mp.items():
        cd = package_of_interest.replace(k, v)
        if cd != package_of_interest:
            candidates.append(cd)
    result = list(set(candidates).intersection(set(all_packages)))
    return result


def get_shifted_package_names(package_of_interest, all_packages):
    left_shift = {
        "q": "  ",
        "w": "q",
        "e": "w",
        "r": "e",
        "t": "r",
        "y": "t",
        "u": "y",
        "i": "u",
        "o": "i",
        "p": "o",
        "a": "",
        "s": "a",
        "d": "s",
        "f": "d",
        "g": "f",
        "h": "g",
        "j": "h",
        "k": "j",
        "l": "k",
        "z": "",
        "x": "z",
        "c": "x",
        "v": "c",
        "b": "v",
        "n": "b",
        "m": "n",
        "1": "`",
        "2": "1",
        "3": "2",
        "4": "3",
        "5": "4",
        "6": "5",
        "7": "6",
        "8": "7",
        "9": "8",
        "0": "9"
    }

    right_shift = {
        "q": "w",
        "w": "e",
        "e": "r",
        "r": "t",
        "t": "y",
        "y": "u",
        "u": "i",
        "i": "o",
        "o": "p",
        "p": "[",
        "a": "s",
        "s": "d",
        "d": "f",
        "f": "g",
        "g": "h",
        "h": "j",
        "j": "k",
        "k": "l",
        "l": ";",
        "z": "x",
        "x": "c",
        "c": "v",
        "v": "b",
        "b": "n",
        "n": "m",
        "m": ",",
        "1": "2",
        "2": "3",
        "3": "4",
        "4": "5",
        "5": "6",
        "6": "7",
        "7": "8",
        "8": "9",
        "9": "0",
        "0": "-"
    }

    lshift = list(package_of_interest)
    rshift = list(package_of_interest)
    for i in range(len(package_of_interest)):
        lshift[i] = left_shift.get(lshift[i], lshift[i])
        rshift[i] = right_shift.get(rshift[i], rshift[i])

    lshift = "".join(lshift)
    rshift = "".join(rshift)

    result = list(set([lshift, rshift]).intersection(set(all_packages)))
    return result


def distance_calculations(package_of_interest, all_packages, max_distance=MAX_DISTANCE):
    """Find packages <= defined edit distance and return sorted list.

    Args:
        package_of_interest (str): package name on which to perform comparison
        all_packages (list): list of all package names
        max_distance (int): the maximum distance that justifies reporting

    Returns:
        list: potential typosquatters
    """
    # Empty list to store similar package names
    similar_package_names = []

    # If the input `max_distance` is 0, determine the appropriate max_distance based on
    # the length of the package name
    if max_distance == 0:
        max_distance = __get_threshold_edit_distance(word_length=len(package_of_interest))

    # Loop thru all package names
    for package in all_packages:

        # Skip if the package is the package of interest
        if package == package_of_interest:
            continue

        # Calculate distance
        distance = Levenshtein.distance(package_of_interest, package)

        # If distance is sufficiently small, add to list
        if distance <= max_distance:
            similar_package_names.append(package)

    # Return alphabetically sorted list of similar package names
    return sorted(similar_package_names)


def __get_order_variants(package):
    import itertools

    words = package.replace("-", "#").replace("_", "#").split("#")

    variants = list()

    if len(words) > 1:
        w1 = words + ["-"] * (len(words) - 1)
        w2 = words + ["_"] * (len(words) - 1)

        w1 = list(itertools.permutations(w1))
        w2 = list(itertools.permutations(w2))

        for v in w1 + w2:
            s = "".join(v)
            if s != package:
                variants.append(s)

    return list(set(variants))


def order_attack_screen(package, all_packages):
    """Find packages that prey on user confusion about order.

    This screen checks for attacks that prey on user confusion
    about word order. For instance, python-nmap vs nmap-python.
    The edit distance is very high, but the conceptual distance is
    close. This function currently identifies only packages that
    capitalize on user confusion about  word order when words are
    separated by dashes or underscores.

    Args:
        package (str): package name on which to perform comparison
        all_packages (list): list of all package names

    Returns:
        list: potential typosquatting packages
    """
    # Check if there is only one total dash or underscore
    # TODO: Consider dealing with other cases (e.g. >=2 dashes)
    squatters = []
    variants = __get_order_variants(package=package)
    if variants:
        # Check if each variant is contained in the full package list
        set_all_packages = set(all_packages)
        for attack in variants:
            if attack in set_all_packages:
                squatters.append(attack)

    return squatters


# def order_attack_screen(package, all_packages):
#     """Find packages that prey on user confusion about order.
#
#     This screen checks for attacks that prey on user confusion
#     about word order. For instance, python-nmap vs nmap-python.
#     The edit distance is very high, but the conceptual distance is
#     close. This function currently identifies only packages that
#     capitalize on user confusion about  word order when words are
#     separated by dashes or underscores.
#
#     Args:
#         package (str): package name on which to perform comparison
#         all_packages (list): list of all package names
#
#     Returns:
#         list: potential typosquatting packages
#     """
#     # Check if there is only one total dash or underscore
#     # TODO: Consider dealing with other cases (e.g. >=2 dashes)
#     squatters = []
#     if package.count("-") + package.count("_") == 1:
#         if package.count("-") == 1:
#             pkg_name_list = package.split("-")
#             reversed_name = pkg_name_list[1] + "-" + pkg_name_list[0]
#             switch_symbol = pkg_name_list[0] + "_" + pkg_name_list[1]
#             switch_symbol_reversed = pkg_name_list[1] + "_" + pkg_name_list[0]
#         else:
#             pkg_name_list = package.split("_")
#             reversed_name = pkg_name_list[1] + "_" + pkg_name_list[0]
#             switch_symbol = pkg_name_list[0] + "-" + pkg_name_list[1]
#             switch_symbol_reversed = pkg_name_list[1] + "-" + pkg_name_list[0]
#         # Check if each attack is contained in the full package list
#         for attack in [reversed_name, switch_symbol, switch_symbol_reversed]:
#             if attack in all_packages:
#                 squatters.append(attack)
#
#     return squatters


def homophone_attack_screen(package_of_interest, all_packages):
    """Find packages that prey on homophone confusion.

    This screen checks for attacks that prey on user confusion
    related to homophones. For instance, 'klumpz' vs. 'clumps'.
    This function helps find confusion attacks, rather than
    misspelling attacks.

    Args:
        package (str): package name on which to perform comparison
        all_packages (list): list of all package names

    Returns:
        list: potential typosquatting packages
    """
    # Empty list to store similar package names
    homophone_package_names = []

    # Calculate metaphone code for package of interest, only once
    # package_of_interest_metaphone = jellyfish.metaphone(package_of_interest)
    package_of_interest_metaphone = jellyfish.match_rating_codex(package_of_interest)

    # Loop thru all package names
    for package in all_packages:

        # Skip if the package is the package of interest
        if package == package_of_interest:
            continue

        # Compare package metaphone code to the metaphone code of the
        # package of interest
        # if jellyfish.metaphone(package) == package_of_interest_metaphone:
        if jellyfish.match_rating_codex(package) == package_of_interest_metaphone:
            homophone_package_names.append(package)

    return homophone_package_names


def whitelist(squat_candidates, whitelist_filename="whitelist.txt"):
    """Remove whitelisted packages from typosquat candidate list.

    Args:
        squat_candidates (dict): dict of packages and potential typosquatters
        whitelist_filename (str): file location for whitelist

    Returns:
        dict: packages and post-whitelist potential typosquatters
    """
    # Create whitelist
    whitelist = []
    with open(whitelist_filename, "r") as file:
        for line in file:
            # Strip out end of line character
            whitelist.append(line.strip("\n"))

    # Remove packages contained in whitelist
    whitelist_set = set(whitelist)
    for pkg in squat_candidates:
        new_squat_candidates_set = set(squat_candidates[pkg]) - whitelist_set
        new_squat_candidates_list = list(new_squat_candidates_set)
        # Update typosquat candidate list
        squat_candidates[pkg] = new_squat_candidates_list

    return squat_candidates
