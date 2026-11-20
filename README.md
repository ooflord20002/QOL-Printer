# QOL-Printer
QOL Marker printer for the recroom revival MeowNet, made by me (@ooflord)

I am aware that the published printer invention has a few issues, I will be fixing them as I go, and if you find any it'd be great if you messaged me, thanks. The issues I know of are:
Transparency symbol not wired to anything in circuit board
Marker #61 does not have a tag
Invention spawns with wrong amount of symbols as the markers have

# THIS PAGE IS A WORK IN PROGRESS, IT'S MAINLY FOR PEOPLE WHO KNOW WHAT THEY'RE DOING
A tutorial will be made sometime very soon, but for now it's mainly for people who know how to use printers already, although if you don't want to wait you can read up on the tutorials posted on old printers like swiftprinter by faustroland and the older shirt printer by McReny

# FYI
When spawning the printer, the first thing you should do is delete the square canvas and spawn your own, as the other one can not be saved because it's part of the invention.

You can generate your tables at the room ^TableGeneration by copying it, and the markers are an invention that come with the printer.

If you want to know if a shirt printer is coming any time soon, yes, I am currently working on it but it will still be a little while.

The printer has a string input for characters. The printer by default has 60 characters inputted, but to use the full 100 you can copy the characters from the text file, or use your own. This option is only for if you are in a room where you want, and can physically fit more markers.

The image data encoded by the main encoder is returned in multiple text files depending on the size of your data blocks, the numbers correspond to the table numbers, and more tables can freely be added if needed.

Currently the main encoder script produces both your image data and the color hex codes, although I have not, and don't intend to make a color importing system in the near future, so if you want to take that step then go right ahead. Also, it is recommended that you import your data tables in a separate room than the printer, and bring them over with an invention because of a current bug that will destroy your room permanently. if you have any other questions you can message ooflordfr on discord.

# Setup
Firstly, in order to be able to generate the encoded text files for images, you will need to have python installed on your computer. You can download python at "https://www.python.org/downloads/".
(Make sure when installing python that you click add to path, so the script knows where to look.)

Within python as of right now only one dependency is needed which can be installed by running "pip install pillow", in the command prompt after python is installed. 
