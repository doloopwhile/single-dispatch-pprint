single-dispatch-pprint
======================

Re-implementation of 'pprint' in Python Standard Library using singledispatch

Almost same as `pprint.*`

    spprint.PrettyPrinter(indent, width, depth, stream)

    spprint.pformat(object, indent, width, depth)

    spprint.pprint(object, stream, indent, width, depth)

However, you can add support for your new types by `format_instance` .

For example:

    import spprint

    class Spam:
        def __init__(self, count, side_dish):
            self.count = count
            self.side_dish = side_dish

        def __repr__(self):
            return "<Spam {}and {}>".format('spam ' * self.count, self.side_dish)

    @spprint.format_instance.register(Spam)
    def format_spam(obj, context):
        w = context.stream.write
        w("<Spam \n")
        for _ in range(obj.count):
            w(' ' * (context.indent + context.indent_per_level))
            w('spam\n')
        w(' ' * (context.indent + context.indent_per_level))
        w('and {}>'.format(obj.side_dish))

    spprint.pprint([Spam(2, 'Egg'), Spam(7, 'Ham')], width=40)

