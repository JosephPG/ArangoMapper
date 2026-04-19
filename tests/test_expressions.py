from app.collections import Device, Location, Route
from app.mapper.expressions import GroupLogicalConnector, Matcher


def test_matcher():
    assert isinstance((Location.id == "1"), Matcher)
    assert isinstance((Location.key != "1"), Matcher)
    assert isinstance((Location.name == "name"), Matcher)
    assert isinstance((Device.weight > 1), Matcher)
    assert isinstance((Device.weight >= 1), Matcher)
    assert isinstance((Device.weight < 1), Matcher)
    assert isinstance((Device.weight <= 1), Matcher)
    assert isinstance((Device.weight.is_in([1, 2, 3])), Matcher)

    assert isinstance((Route.id_from == "11"), Matcher)
    assert isinstance((Route.id_to == "12"), Matcher)


def test_group_logical_connector():
    assert isinstance(
        (Location.id == "1") & (Location.name == "name"), GroupLogicalConnector
    )
    assert isinstance(
        (Route.id_from == "11") | (Route.id_to == "11"), GroupLogicalConnector
    )

    cond: GroupLogicalConnector = (Location.id == "1") | (Location.id == "2")
    cond = cond & ((Device.name == "name") & (Device.type == "type"))
    cond = cond | (Route.id_from == "11")

    assert isinstance(cond, GroupLogicalConnector)

    assert isinstance(cond.left, GroupLogicalConnector)
    assert isinstance(cond.left.left, GroupLogicalConnector)
    assert isinstance(cond.left.left.left, Matcher)
    assert isinstance(cond.left.left.right, Matcher)

    assert cond.left.left.left.field.target == "_id"
    assert cond.left.left.right.field.target == "_id"

    assert isinstance(cond.left.right, GroupLogicalConnector)
    assert isinstance(cond.left.right.left, Matcher)
    assert isinstance(cond.left.right.right, Matcher)

    assert cond.left.right.left.field.target == "name"
    assert cond.left.right.right.field.target == "type"

    assert isinstance(cond.right, Matcher)
    assert cond.right.field.target == "_from"
