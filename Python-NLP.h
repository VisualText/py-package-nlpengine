#pragma once

#include <string>
// #include <pybind11/pybind11.h>

#include "lite/nlp_engine.h"
#include "lite/vtrun.h"     // Include NLP++ runtime manager.   // 09/25/20 AM

#ifdef LINUX
#include <unistd.h>
#define GetCurrentDir getcwd
#else
#include <direct.h>
#define GetCurrentDir _getcwd
#endif
#include<iostream>


extern "C" __declspec(dllexport) void setWorkingFolder(const char* folder);
extern "C" __declspec(dllexport) const char* analyze(const char* parser, const char* inputStr);



//namespace py = pybind11;
//
//PYBIND11_MODULE(Python-NLP, m) {
//    m.doc() = "pybind11 example plugin"; // optional module docstring
//
//    m.def("analyze", &analyze, "A function that adds two numbers");
//    m.def("setWorkingFolder", &setWorkingFolder, "A function that adds two numbers");
//}