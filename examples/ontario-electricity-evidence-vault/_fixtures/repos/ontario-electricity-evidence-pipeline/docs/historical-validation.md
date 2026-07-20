# Historical validation

The fixture accepts a historical series only when it has at least one positive annual-demand row
and each monthly peak is greater than its corresponding minimum. Failed rows remain available for
review; the fixture does not coerce values or produce forward-looking output.
