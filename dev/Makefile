IMAGES=uas-mgr-testing uas-mgr-coverage

.PHONY: help
help:
	@echo
	@echo "Welcome to uas-mgr developement"
	@echo
	@echo "Available targets:"
	@echo "    clean-images      - removes development Docker images"
	@echo
	@echo "    Testing:"
	@echo "    unit-tests        - run all unit tests and linting"
	@echo "    functional-tests  - run the functional tests"
	@echo "                        (must be run from activate virtualenv with all of"
	@echo "                        trebuchet test dependencies installed)"
	@echo

.PHONY: clean-images
clean-images:
	docker rmi -f $(IMAGES)

.PHONY: functional-tests
functional-tests:
	@docker build -t uas-mgr-testing --target testing . && docker run -it --rm uas-mgr-testing

.PHONY: unit-tests
unit-tests:
	@docker build -t uas-mgr-coverage --target coverage . && docker run -it --rm uas-mgr-coverage
