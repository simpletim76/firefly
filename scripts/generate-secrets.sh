#!/bin/bash

echo "=== Project Firefly - Secret Key Generator ==="
echo ""

# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

echo "Generated SECRET_KEY:"
echo "SECRET_KEY=$SECRET_KEY"
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "WARNING: .env file already exists!"
    read -p "Overwrite SECRET_KEY in .env? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Update SECRET_KEY in existing .env
        if grep -q "SECRET_KEY=" .env; then
            sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            echo "✓ Updated SECRET_KEY in .env"
        else
            echo "SECRET_KEY=$SECRET_KEY" >> .env
            echo "✓ Added SECRET_KEY to .env"
        fi
    fi
else
    # Create new .env from example
    cp .env.example .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    echo "✓ Created .env with generated SECRET_KEY"
fi

echo ""
echo "Keep this key secure! Add .env to .gitignore"
