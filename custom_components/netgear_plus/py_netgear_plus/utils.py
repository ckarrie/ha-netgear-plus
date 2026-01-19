"""Utility functions."""


def get_all_child_classes_dict(
    parent_class: type[object], filter_attr: str | None = None
) -> dict[str, type[object]]:
    """
    Retrieve a dictionary of all subclasses of the given parent class.

    The key is the subclass's `filter_attr` attribute if provided. Otherwise,
    it includes all subclasses using their class name.

    If a subclass does not have the `filter_attr` attribute or it is empty,
    it is skipped from the dictionary, but its children are still included.

    :param parent_class: The parent class to find subclasses of.
    :param filter_attr: The attribute to filter subclasses (default: None,
        meaning include all).
    :return: A dictionary {subclass.filter_attr: subclass_object} if
        filter_attr is provided, otherwise {subclass.__name__: subclass_object}.
    """
    subclasses_dict: dict[str, type[object]] = {}

    for subclass in parent_class.__subclasses__():
        # Recursively get child subclasses first
        subclasses_dict.update(get_all_child_classes_dict(subclass, filter_attr))

        if filter_attr:
            attr_value = getattr(subclass, filter_attr, None)
            if isinstance(attr_value, str) and attr_value:
                subclasses_dict[attr_value] = subclass
        else:
            subclasses_dict[subclass.__name__] = (
                subclass  # Use class name if no filter attribute
            )

    return subclasses_dict


def get_all_child_classes_list(
    parent_class: type[object], filter_attr: str | None = None
) -> list[type[object]]:
    """
    Retrieve a list of all subclasses of the given parent class.

    If `filter_attr` is provided, only subclasses with a non-empty `filter_attr`
    value are returned.

    :param parent_class: The parent class to find subclasses of.
    :param filter_attr: The attribute to filter subclasses (default: None,
        meaning include all).
    :return: A list of subclass objects.
    """
    subclasses_list: list[type[object]] = []

    for subclass in parent_class.__subclasses__():
        # Recursively get child subclasses first
        subclasses_list.extend(get_all_child_classes_list(subclass, filter_attr))

        if filter_attr:
            attr_value = getattr(subclass, filter_attr, None)
            if isinstance(attr_value, str) and attr_value:
                subclasses_list.append(subclass)
        else:
            subclasses_list.append(subclass)  # Include all if no filter attribute

    return subclasses_list
