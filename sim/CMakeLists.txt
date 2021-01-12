cmake_minimum_required(VERSION 3.16)
# use cmake policy to make option() to honor normal variables
# http://shadow.nd.rl.ac.uk/ICP_Binaries/CMake/doc/cmake/html/policy/CMP0077.html
set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)
project(bentobox)

## Executable
set(TARGET_SIM ${PROJECT_NAME})
set(TARGET_TEST "${PROJECT_NAME}-test")
set(TARGETS ${TARGET_SIM} ${TARGET_TEST})
# target bento simulator's executables to c++ 20
set(CMAKE_CXX_STANDARD 20)
add_executable(${TARGET_SIM}
    src/main.cpp
    src/system/render.cpp
)
target_include_directories(${TARGET_SIM}
    PUBLIC include
)

add_executable(${TARGET_TEST}
    src/main.test.cpp
    src/index/componentType.test.cpp
)
target_include_directories(${TARGET_TEST}
    PUBLIC include
)

add_subdirectory("lib/core")
target_link_libraries(${TARGET_SIM}
    PRIVATE bento::core
)
target_link_libraries(${TARGET_TEST}
    PRIVATE bento::core
    # When --whole-archive is needed to ensure that core-test's tests are not lost when
    # they are linked to the test target. The core-test's tests are lost because they
    # are not referenced. This flag ensures that the tests are retained.
    PRIVATE -Wl,--whole-archive bento::core-test -Wl,--no-whole-archive
)

## Library Dependencies
# fetch dependencies
include("dependencies.cmake")

# GRPC/Protobuf
# link protobuf/grpc libraries
foreach(target IN ITEMS ${TARGETS})
    target_include_directories(${target} PRIVATE "${PROTOBUF_DIR}/src")
    target_link_libraries(${target} PRIVATE libprotobuf grpc++ grpc++_reflection)
endforeach()

# Compile and link protobuf c++ bindings from protobuf definitions
get_filename_component(PROTOS_DIR "../protos" ABSOLUTE)
# target directory to write protobuf bindings to
set(PROTO_BINDS_DIR "${CMAKE_CURRENT_BINARY_DIR}/protos")
file(MAKE_DIRECTORY ${PROTO_BINDS_DIR})
# list protobuf definitions in protos/
file(GLOB PROTO_DEFS "${PROTOS_DIR}/bento/protos/*.proto")
# replace .proto with .pb.cc and .pb.h
string(REPLACE "${PROTOS_DIR}" "${PROTO_BINDS_DIR}" PROTO_BINDS "${PROTO_DEFS}")
string(REPLACE ".proto" ".pb.cc" PROTO_BIND_SOURCES "${PROTO_BINDS}")
string(REPLACE ".proto" ".grpc.pb.cc" PROTO_GRPC_SOURCES "${PROTO_BINDS}")
string(REPLACE ".proto" ".pb.h" PROTO_BIND_HEADERS "${PROTO_BINDS}")
# run protoc with grpc_cpp_plugin to generate c++ bindings
add_custom_command(
    OUTPUT ${PROTO_BIND_HEADERS} ${PROTO_BIND_SOURCES} ${PROTO_GRPC_SOURCES}
    COMMAND $<TARGET_FILE:protoc>
    ARGS
        -I ${PROTOS_DIR}
        --grpc_out ${PROTO_BINDS_DIR}
        --cpp_out ${PROTO_BINDS_DIR}
        --plugin=protoc-gen-grpc=$<TARGET_FILE:grpc_cpp_plugin>
        ${PROTO_DEFS}
    DEPENDS ${PROTO_DEFS} $<TARGET_FILE:protoc> $<TARGET_FILE:grpc_cpp_plugin>
)
foreach(target IN ITEMS ${TARGETS})
    target_sources(${target} PRIVATE ${PROTO_BIND_SOURCES} ${PROTO_GRPC_SOURCES})
    target_include_directories(${target} PRIVATE ${PROTO_BINDS_DIR})
endforeach()

## Test Dependencies
# link googletest
target_link_libraries(${TARGET_TEST} PRIVATE -Wl,--no-whole-archive gtest_main)