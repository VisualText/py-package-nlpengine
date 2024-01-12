#include "Python-NLP.h"

std::unique_ptr<NLP_ENGINE> nlpEngine;

extern "C" __declspec(dllexport) void setWorkingFolder(const char* folder)
{
	nlpEngine = std::make_unique<NLP_ENGINE>(folder);
}

extern "C" __declspec(dllexport) const char* analyze(const char* parser, const char* inputStr)
{
	std::istringstream ssi1(inputStr);
	std::ostringstream sso1;
//	std::_t_cout << _T("[input: ") << ssi1.str() << _T("]") << std::endl;

	char* _parser = new char[strlen(parser) + 1];
	strcpy(_parser, parser);

//	std::_t_cout << _T("[parser: ") << _parser << _T("]") << std::endl;

	nlpEngine->analyze(_parser, &ssi1, &sso1);

//	std::_t_cout << _T("[output: ") << sso1.str() << _T("]") << std::endl;

	static std::string str_data = sso1.str();

	return str_data.c_str();
}