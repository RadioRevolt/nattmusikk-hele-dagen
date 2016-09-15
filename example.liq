#!/usr/bin/liquidsoap

# Just for testing purposes, you can turn off logging
# to a file and instead log to stdout, but in the real
# world, you'll want to log to a file so you can understand
# what went wrong in case of errors.

set("log.stdout", true)
set("log.file", false)

# Create a socket file which the external script can connect to
set("server.socket", true)
set("server.socket.path", "/tmp/testing_socket")

# Create the interactive bool which we'll change from the
# request2liquidsoap.py script.
# "variable_name" is the name which shall be used by the
# the script to refer to this variable. The second argument 
# is the default value, right after startup

nightmusic_all_day = interactive.bool("variable_name", false)

# As nightmusic, we'll play a high-pitched sine sound

nightmusic = sine(amplitude=0.7, 880.)
nightmusic = mksafe(nightmusic)

# As our default, we'll play a sine sound one octave lower
default = sine(amplitude=0.7, 440.)

# Switch between the two streams based on the interactive bool
# and the current time of day.

output_stream = switch(track_sensitive=false, [
    ({0h-7h}, nightmusic),
    (nightmusic_all_day, nightmusic),  # this must be a separate entry, using "or" yields errors because appaerantly this isn't really a bool?
    ({ true }, default)
])
output_stream = mksafe(output_stream)


out(output_stream)
