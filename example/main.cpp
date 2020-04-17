#include <iostream>
#include <memory>

#include "resource_builder/resources.h"

/**
 * A simple program to show how to use resource builder script and how to use embedded resources in code.
 * Data is included "AS IS. For example, PNG images are included as raw data. To get actual image you will
 * need a library to load image from memory (e.g. stb_image). Raw text data can be used without processing.
 */
int main() {
    const uint8_t* data = ResourceBuilder::get_resource_data(ResourceBuilder::ResId::__ICONS_R64_SAMPLE_PNG);
    uint32_t sz = ResourceBuilder::get_resource_size(ResourceBuilder::ResId::__ICONS_R64_SAMPLE_PNG);

    std::cout << "Included icon is "<<sz<<" bytes long\n";
    //Expected output:
    //Included icon is 3571 bytes long

    // This is important when embedding string data. It is not guaranteed that we can read byte after
    // last character and if it is even '\0'. So we need to copy data and set null byte manually
    auto text = ResourceBuilder::get_resource_text(ResourceBuilder::ResId::__TXT_HELLO_TXT);

    //new line is not added at the end because text file has one empty line at the end
    std::cout << "Included text is "<< text;
    //Expected output:
    //Included text is Hello world from embedded resource!

    return 0;
}
