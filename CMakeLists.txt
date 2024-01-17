cmake_minimum_required(VERSION 3.15)
project(${SKBUILD_PROJECT_NAME} LANGUAGES CXX)

add_subdirectory(nlp-engine)
include_directories(nlp-engine/cs/include)
include_directories(nlp-engine/include)
include_directories(nlp-engine/include/Api)
include_directories(nlp-engine/include/Api/lite)
include_directories(nlp-engine/include)

if(WIN32)
  add_definitions( -DMSVC_VERSION=${MSVC_VERSION} -D_CRT_SECURE_NO_WARNINGS )
else()
  # Not the greatest way to define "not Windows"!
  add_definitions( -DLINUX -Wno-write-strings -Wno-deprecated)
endif()

set_property(TARGET prim PROPERTY POSITION_INDEPENDENT_CODE on)
set_property(TARGET kbm PROPERTY POSITION_INDEPENDENT_CODE on)
set_property(TARGET consh PROPERTY POSITION_INDEPENDENT_CODE on)
set_property(TARGET words PROPERTY POSITION_INDEPENDENT_CODE on)
set_property(TARGET lite PROPERTY POSITION_INDEPENDENT_CODE on)

find_package(Python 3.8 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(bindings NB_STATIC bindings.cpp)
target_link_libraries(bindings PRIVATE prim kbm consh words lite)
install(TARGETS bindings LIBRARY DESTINATION NLPPlus)
