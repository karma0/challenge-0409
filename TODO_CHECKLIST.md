# TODO Checklist: Ensure Challenge Spec Compliance

## Challenge Spec Requirements
Per `challenge_spec.md`, the application must:
1. Design a function that accepts two inputs: a user's question and a context paragraph
2. Integrate a language model API (e.g., OpenAI's chat completion) to process the inputs and generate an answer
3. Preprocess the inputs as necessary to improve the model's understanding
4. Output should be formatted and returned as the answer to the user's question

## Current Status Review

### Core Requirements (Verify Compliance)
- [ ] Verify `answer_question(question, context)` function exists and works
- [ ] Verify OpenAI API integration is functional
- [ ] Verify input preprocessing is appropriate
- [ ] Verify output is properly formatted

### Additional Features (Keep but Document as Extensions)
- Security features (input validation, output sanitization)
- Rate limiting
- Configuration options
- Docker support
- Development tooling (linting, testing)

## Tasks to Ensure Spec Compliance

### Phase 1: Core Function Verification
1. [ ] Review `answer_question()` signature - ensure it accepts question and context
2. [ ] Verify the function can be called with just two parameters
3. [ ] Ensure default configuration works without explicit config
4. [ ] Test basic usage matches spec example

### Phase 2: Documentation Updates
5. [ ] Update README.md to clearly show:
   - [ ] Primary usage that matches spec (simple two-parameter call)
   - [ ] Mark additional features as "Extensions" or "Additional Features"
   - [ ] Ensure quickstart example matches spec requirements
6. [ ] Update function docstrings to emphasize spec compliance

### Phase 3: Simplify Default Usage
7. [ ] Ensure `answer_question()` works with minimal imports
8. [ ] Make config optional with sensible defaults
9. [ ] Consider adding a simple example that exactly matches spec

### Phase 4: Test Coverage for Spec
10. [ ] Add/verify test that uses function exactly as spec describes
11. [ ] Ensure basic preprocessing tests exist
12. [ ] Verify output formatting test exists

### Phase 5: Example Improvements
13. [ ] Create a minimal example script showing spec usage:
    ```python
    from qa_chain import answer_question

    question = "What is the capital of France?"
    context = "Paris is the capital of France."
    answer = answer_question(question, context)
    print(answer)
    ```

### Phase 6: Verify Development Environment
14. [ ] Ensure Makefile has all development commands:
    - [ ] `make lint` - for linting
    - [ ] `make fix` - for fixing lint issues
    - [ ] `make test` - for running tests
    - [ ] `make format` - for code formatting
15. [ ] Verify pre-commit hooks work for development

### Phase 7: Final Verification
16. [ ] Run minimal example to verify spec compliance
17. [ ] Ensure all 4 spec requirements are clearly met:
    - [ ] Two-input function ✓
    - [ ] LLM integration ✓
    - [ ] Input preprocessing ✓
    - [ ] Formatted output ✓
18. [ ] Document that security/rate-limiting are production-ready additions

## Approach
Rather than removing features, we'll:
1. Ensure the core spec requirements are clearly met
2. Present the simplest usage first in documentation
3. Position additional features as "production-ready enhancements"
4. Keep all development tooling for maintainability

This approach maintains all the good work done while ensuring clear spec compliance.
