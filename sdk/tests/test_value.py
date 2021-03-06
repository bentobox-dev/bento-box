#
# Bentobox
# SDK - Value Tests
#

from bento.value import *
from bento.protos.types_pb2 import Type

wrap_primitive_types = [
    (1, Type.Primitive.INT32),
    (-1, Type.Primitive.INT32),
    # 2**31-1 should be the largest integer representable in int32
    (-(2 ** 31), Type.Primitive.INT32),
    (2 ** 31 - 1, Type.Primitive.INT32),
    (2 ** 31, Type.Primitive.INT64),
    ("test", Type.Primitive.STRING),
    (0.2, Type.Primitive.FLOAT64),
    (True, Type.Primitive.BOOL),
    (None, Type.Primitive.INVALID),
    ([0.2], Type.Primitive.INVALID),
]


def test_wrap_primitive():
    for val, expect_type in wrap_primitive_types:
        try:
            proto = wrap_primitive(val)
        except TypeError:
            assert expect_type == Type.Primitive.INVALID
            continue
        # check wrapped primitive
        dtype = proto.data_type.primitive
        assert dtype == expect_type
        if dtype == Type.Primitive.INT32:
            assert proto.primitive.int_32 == val
        elif dtype == Type.Primitive.INT64:
            assert proto.primitive.int_64 == val
        elif dtype == Type.Primitive.FLOAT64:
            assert proto.primitive.float_64 == val
        elif dtype == Type.Primitive.STRING:
            assert proto.primitive.str_val == val
        elif dtype == Type.Primitive.BOOL:
            assert proto.primitive.boolean == val
        else:
            raise TypeError(f"Untested data type {dtype}")


def test_wrap():
    # wrap() should support everything wrap_primitive() can wrap
    wrap_val_types = wrap_primitive_types[:-1] + [
        # multi dim numpy array
        (
            np.ones((2, 1, 3), dtype=np.int32),
            Type.Array(dimensions=(2, 1, 3), element_type=Type.Primitive.INT32),
        ),
        # single dim list
        (
            ["yes", "no"],
            Type.Array(dimensions=(2,), element_type=Type.Primitive.STRING),
        ),
        # multi dim list
        (
            [[True, False], [False, True]],
            Type.Array(dimensions=(2, 2), element_type=Type.Primitive.BOOL),
        ),
        # finite generator
        (
            (x for x in [1.2, 3.4]),
            Type.Array(dimensions=(2,), element_type=Type.Primitive.FLOAT64),
        ),
        # bad: list with dim mismatch
        ([[True, False], [True]], Type.Array(element_type=Type.Primitive.INVALID)),
    ]

    for val, expect_type in wrap_val_types:
        try:
            proto = wrap(val)
        except TypeError:
            assert expect_type in [
                Type.Primitive.INVALID,
                Type.Array(element_type=Type.Primitive.INVALID),
            ]
            continue
        # skip primitives as already tested in test_wrap_primitive()
        if proto.data_type.WhichOneof("kind") == "primitive":
            continue
        # check wrapped value's shape
        dtype = proto.data_type.array
        assert dtype == expect_type
        assert len(proto.array.values) == sum(expect_type.dimensions)
        # check wrapped primitive's data types are identical
        assert len(set(p.WhichOneof("value") for p in proto.array.values)) == 1

    # do nothing if given an already wrapped value protobuf message
    wrapped_bool = wrap_primitive(True)
    assert wrap(wrapped_bool) == wrapped_bool


unwrap_primitive_values = [(wrap(v), v) for v, _ in wrap_primitive_types[:-2]] + [
    # test error handling with invalid data types
    (Value(data_type=Type(primitive=Type.Primitive.INVALID)), None),
    (wrap([1, 2, 3]), None),
]


def test_unwrap_primitive():
    # :-2 skip the last to invalid entries
    # (Value proto, native value)
    for value, expected_val in unwrap_primitive_values:
        try:
            actual_val = unwrap_primitive(value)
        except TypeError:
            # check for TypeError on non primitive data type
            assert value.data_type.WhichOneof("kind") != "primitive"
            continue
        except ValueError:
            # check for ValueError on invald data type
            assert value.data_type.primitive == Type.Primitive.INVALID
            continue

        assert actual_val == expected_val


def test_unwrap():
    # unwrap() should support everything unwrap_primitive() can wrap
    # :-2 skip the last 2 invalid entiries
    # Value proto, expected value
    unwrap_values = [(wrap(val), val) for val, _ in wrap_primitive_types[:-2]] + [
        (
            wrap(np.ones((2, 1, 3), dtype=np.int32)),
            np.ones((2, 1, 3), dtype=np.int32),
        ),
        (
            wrap(np.asarray(["yes", "no"])),
            np.asarray(["yes", "no"]),
        ),
        (
            wrap(np.asarray([[True, False], [False, True]])),
            np.asarray([[True, False], [False, True]]),
        ),
        (wrap(x for x in [1.2, 3.4]), np.asarray([x for x in [1.2, 3.4]])),
        # bad: invald data type
        (Value(data_type=Type(primitive=Type.Primitive.INVALID)), None),
        # bad: invald data type kind
        (Value(), None),
    ]
    for value, expected_val in unwrap_values:
        try:
            actual_val = unwrap(value)
        except TypeError:
            # check for TypeError on invald data type kind
            assert value.data_type.WhichOneof("kind") is None
            continue
        except ValueError:
            # check for Value on invald data type
            assert value.data_type.primitive == Type.Primitive.INVALID
            continue
        if isinstance(expected_val, np.ndarray):
            assert (actual_val == expected_val).all()
        else:
            assert actual_val == expected_val
