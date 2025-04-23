import csv

with open('Listing250423.txt', encoding='utf-8') as infile, \
     open('data.csv', 'w', newline='', encoding='utf-8') as outfile:

    writer = csv.writer(outfile)
    header_written = False

    for line in infile:
        if not line.startswith('|'):
            continue

        # skip dashed‐line rows
        if set(line.strip()) <= {'|', '-'}:
            continue

        # strip outer pipes, split on '|' to handle multi-column exports
        row = [cell for cell in (line.strip().strip('|').split('|')) if cell]
        if not header_written:
            writer.writerow(row)
            header_written = True
        else:
            writer.writerow(row)
