#!/usr/bin/env python3.4

from tests.lawful import test, run_tests

import judged
from judged import tokenizer
from judged import parser
from judged import context
from judged import actions

import io
from pathlib import Path
import difflib

def compare_clauses(a, b):
    if a.head == b.head:
        if a.body == b.body:
            if a.sentence.create_bdd() == b.sentence.create_bdd():
                return True
    return False

def compare_lists(a, b):
    if len(a) != len(b):
        return False
    for p in zip(a, b):
        if not compare_clauses(*p):
            return False
    return True

def make_suite(path, root, context_type):
    @test.complex
    def suite():
        expect_file = root / (path.stem + '.txt')
        context = context_type()

        expected = []
        output = []

        with path.open() as f:
            for action in parser.parse(f):
                try:
                    if isinstance(action, actions.QueryAction):
                        for a in action.perform(context).answers:
                            output.append(a.clause)
                    else:
                        action.perform(context)
                except judged.JudgedError as e:
                    raise AssertionError from e

        with expect_file.open() as f:
            for action in parser.parse(f):
                if isinstance(action, actions.AssertAction):
                    expected.append(action.clause)
                else:
                    raise AssertionError("Programmer error: action '{}' in expectations file for this case".format(
                        action
                    ))

        expected.sort(key=lambda c: c.id)
        output.sort(key=lambda c: c.id)

        if not compare_lists(output, expected):
            output_lines = ''.join("{}.\n".format(a) for a in output).splitlines(keepends=True)
            expected_lines = ''.join("{}.\n".format(a) for a in expected).splitlines(keepends=True)
            d = difflib.Differ()
            result = ['--- output\n','+++ expected\n', '\n']
            result.extend(d.compare(output_lines, expected_lines))
            message = ''.join(result)
            assert compare_lists(output, expected), message
    suite.__name__ = path.stem


for case in Path('tests/cases/deterministic').glob('*.dl'):
    make_suite(case, Path('tests/cases/deterministic'), context.DeterministicContext)

for case in Path('tests/cases/exact').glob('*.dl'):
    make_suite(case, Path('tests/cases/exact'), context.ExactContext)

for case in Path('tests/cases/montecarlo').glob('*.dl'):
    make_suite(case, Path('tests/cases/montecarlo'), context.MontecarloContext)
