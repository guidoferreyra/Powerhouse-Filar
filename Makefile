SOURCES=$(shell python3 scripts/read-config.py --sources )
FAMILY=$(shell python3 scripts/read-config.py --family )


help:
	@echo "###"
	@echo "# Build targets for $(FAMILY)"
	@echo "###"
	@echo
	@echo "  make build:  Builds the fonts and places them in the fonts/ directory"
	@echo "  make test:   Tests the fonts with fontbakery"
	@echo

build: build.stamp

dev: venv .init.stamp
	. venv/bin/activate; rm -rf fonts/; python3 scripts/buildSuperFont.py;

venv: venv/touchfile

statics: venv .init.stamp
	. venv/bin/activate; rm -rf fonts/; python3 scripts/buildFonts.py;

build.stamp: venv .init.stamp
	. venv/bin/activate; rm -rf fonts/; python3 scripts/buildSuperFont.py; python3 scripts/buildFonts.py;

build.stampORIG: venv .init.stamp
	. venv/bin/activate; rm -rf fonts/; gftools builder sources/config.yaml && touch build.stamp; rm -rf instance_ufo/; python3 scripts/makeWebfonts.py

.init.stamp: venv
	. venv/bin/activate;

venv/touchfile: requirements.txt
	test -d venv || python3 -m venv venv
	. venv/bin/activate; pip install -Ur requirements.txt
	touch venv/touchfile

test: venv
	. venv/bin/activate; mkdir -p out/ out/fontbakery; fontbakery check-universal -l WARN --succinct --html out/fontbakery/statics-report.html --ghmarkdown out/fontbakery/statics-report.md $(shell find fonts/ttf -type f); fontbakery check-universal -l WARN --succinct --html out/fontbakery/variable-report.html --ghmarkdown out/fontbakery/variable-report.md $(shell find fonts/ttf-vf -type f)

clean:
	rm -rf venv
	find . -name "*.pyc" | xargs rm delete
