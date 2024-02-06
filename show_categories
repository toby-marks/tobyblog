#!/bin/zsh

# Enable extended globbing
setopt extended_glob

# Initialize a temporary file to hold all categories
temp_file=$(mktemp)

# Iterate over all markdown files in the current directory and subdirectories
for file in **/*.md(.); do
    # Extract the categories, remove the brackets, quotations, extra spaces, and convert to lowercase
    awk -F'categories = ' '/^categories =/ { gsub(/\[|\]|"/, "", $2); print tolower($2) }' "$file" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' >> "$temp_file"
done

# Sort the list, remove duplicates, and store in a file
sort "$temp_file" | uniq > unique_sorted_categories.txt

# Clean up the temporary file
rm "$temp_file"

# Print the result
echo "Unique, sorted categories from all files in lowercase:"
cat unique_sorted_categories.txt