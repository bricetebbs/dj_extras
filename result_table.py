from forms import ParameterTypes
import sqlite3


DEF_SQLITE_TYPES = {
    ParameterTypes.INTEGER : "INT",
    ParameterTypes.FLOAT : "REAL",
    ParameterTypes.BOOLEAN: "INT",
    ParameterTypes.STRING: "TEXT",
    ParameterTypes.LABEL: "TEXT",
    ParameterTypes.URL: "TEXT",
    ParameterTypes.ENUM: "INT",
}

def get_sqlite_term(info):
    get_type = DEF_SQLITE_TYPES.get(info['kind'], 'TEXT')
    return '"%s" %s' % (info['name'], get_type)



def format_location(tup):
    from hn_utils.sequence_store import ucsc_browser_name_for_sequence_id
    return "%s:%d-%d" % (ucsc_browser_name_for_sequence_id(tup[0]),tup[1], tup[2])

def format_html_url(s):
    if "|" in s:
        label, link = s.split('|',1)
    else:
        label = "Link"
        link = s
    return  "<a target='_blank' href='%s'>%s</a>" % (link, label)


FORMATTERS = dict(location=format_location,
                  html_url=format_html_url)

class ResultTableVisibility(object):
    VISIBLE = 0
    HIDDEN = 10
    LIMITED = 20  # Stuff already in the normal  description

    CHOICES = (
        (VISIBLE, "Visible"),
        (HIDDEN, "Hidden"),
        (LIMITED, "Limited"),
    )



class ResultTableIndex(object):
    NONE = 0
    NON_UNIQUE = 5
    UNIQUE = 10

    CHOICES = (
        (NONE, "None"),
        (NON_UNIQUE, "Non Unique"),
        (UNIQUE, "Unique"),
        )


class ResultInterface(object):

    def _setup_access(self):
        pass



    def __init__(self, file_path, headers):
        self.headers = [dict(name='rowid',
                        visibility=ResultTableVisibility.HIDDEN,
                        display_name='Row ID',
                        kind = ParameterTypes.INTEGER)]


        self.headers.extend(headers)
        self.file_path = file_path

        self.view_info = None

        self.header_dict = dict(rowid=self.headers[0])
        self.header_indicies = dict(rowid=0)

        for idx, x in enumerate(self.headers):
            self.header_dict[x['name']] = x
            self.header_indicies[x['name']] = idx


        self.db = sqlite3.connect(self.file_path)
        self.cur = self.db.cursor()
        self._setup_access()

    def get_display_headers(self):
        def get_display_name(v):
            if 'display_name' in v:
                return v['display_name']
            return self.header_dict[v['name']]['display_name']

        if not self.view_info:
            return  [(x['name'],x['display_name']) for x in self.headers if x.get('visibility',-1) != ResultTableVisibility.HIDDEN]
        else:
            return [(x['name'], get_display_name(x)) for x in self.view_info]


    def close(self):
        self.cur.close()
        self.db.commit()
        self.db.close()


OP_OP_DICT = dict(GE='>=', LE='<=', EQ='=', IN='IN')
ESCAPED_TYPES = [ParameterTypes.STRING, ParameterTypes.URL, ParameterTypes.URL]


class ResultReadInterface(ResultInterface):

    def _setup_access(self):
        self.filters = []
        self.filter_clause = ""

    def _get_all_headers(self):
        return ",".join([x['name'] for x in self.headers])

    def _tuple_to_dict(self, tup, show_all=False):
        dd = {}
        for idx, h in enumerate(self.headers):
            if show_all or self.headers[idx].get('visibility',0) != ResultTableVisibility.HIDDEN:
                dd[str(h['name'])] = tup[idx]
        return dd

    def _interpret_term(self, term,idx, for_csv):
        if self.headers[idx]['kind'] == ParameterTypes.ENUM:
            term = dict(self.headers[idx]['enum_labels'])[int(term)]

        if self.headers[idx]['kind'] == ParameterTypes.URL:
            if "|" in term:
                label, link = term.split('|',1)
            else:
                label = "Link"
                link = term
            term = "<a target='_blank' href='%s'>%s</a>" % (link, label) if not for_csv else link
        return term


    def _get_filter_for_ops(self, p, escape_value=True):
        if escape_value:
            return '"%s" %s \'%s\'' % (p[0], OP_OP_DICT[p[1]], str(p[2]))
        else:
            return '"%s" %s %s' % (p[0], OP_OP_DICT[p[1]], str(p[2]))

    def add_filter(self, filter_def):
        field, op , value = filter_def.split('~') if type(filter_def) in [str, unicode] else filter_def
        if field in self.header_dict:

            self.filters.append((field, op, value))
            needs_escape = self.header_dict[field]['kind'] in ESCAPED_TYPES
            self.filter_clause = "WHERE %s" % " AND ".join([self._get_filter_for_ops(f, escape_value=needs_escape) for f in self.filters])

    def clear_filters(self):
        self.filters = []
        self.filter_clause = ""

    def get_result_tuples(self, sort_terms=(), offset=0, limit=0):

        sort_clause = ""
        if sort_terms:
            sort_clause = "ORDER BY " + ", ".join(['"%s" %s' % term for term in sort_terms])
        if limit:
            sort_clause += " LIMIT %d" % limit
        if offset:
            sort_clause += " OFFSET %d" % offset

        full_clause = "SELECT rowid,* from RESULT %s %s;" % (self.filter_clause,  sort_clause)

        try:
            self.cur.execute(full_clause)
            return self.cur.fetchall()
        except:
            return ()


    def get_dict_for_tuple(self, tup):
        return self._tuple_to_dict(tup, show_all=True)

    def get_item_count(self):
        try:
            sql= "SELECT COUNT(*) from RESULT %s;" % self.filter_clause
            self.cur.execute(sql)

            return self.cur.fetchone()[0]
        except:
            return 0

    def get_result_tuple(self, item_index):
        sql= "SELECT rowid,* FROM RESULT WHERE rowid=?"

        self.cur.execute(sql,(item_index,))
        return self.cur.fetchone()

    def get_result_dict(self, item_index):
        return self._tuple_to_dict(self.get_result_tuple(item_index))

    def get_result_info_at_index(self, item_index):
        tup = self.get_result_tuple(item_index)
        rval = []
        for idx,item in enumerate(tup):
            if self.headers[idx].get('visibility',0) != ResultTableVisibility.VISIBLE:
                continue
            rval.append((self.headers[idx]['display_name'], self._interpret_term(tup[idx], idx, False)))
        return rval


    def set_view_info(self, view_info):
        self.view_info = view_info


    def _get_formatted_item(self, x, value, for_csv=False):

        if x.get('format', None):
            fmt = x['format']
            if fmt in FORMATTERS:
                term = FORMATTERS[fmt](value)
            elif callable(fmt):
                term = fmt(value)
            else:
                term = fmt % value
            return term


        elif x['kind'] == ParameterTypes.BOOLEAN:
            return "Y" if int(value) else "N"

        elif x['kind'] == ParameterTypes.ENUM:
            return dict(x['enum_labels'])[int(value)]

        elif x['kind'] == ParameterTypes.URL:
            if "|" in value:
                label, link = value.split('|',1)
            else:
                label = "Link"
                link = value
            return "<a target='_blank' href='%s'>%s</a>" % (link, label) if not for_csv else link
        return unicode(value)


    def interpret_tuple(self, tup, for_csv=False, show_hidden=False):
        l = []
        #
        # Allow for a fancier interpretation of the data than normal
        #
        if self.view_info:
            for view_item in self.view_info:
                if view_item.get('group', None):
                    # assemble the group items
                    items = tuple([tup[self.header_indicies[term]] for term in view_item['group']])
                else:
                    items = tup[self.header_indicies[view_item['name']]]

                # combine info from the view and the data description to get the control info
                info = dict(self.header_dict.get(view_item['name'],{}).items() + view_item.items())
                term = self._get_formatted_item(info, items)
                l.append(term)
        else:
            for idx, term in enumerate(tup):
                if not show_hidden and self.headers[idx].get('visibility',0) ==  ResultTableVisibility.HIDDEN:
                    continue
                term = self._get_formatted_item(self.headers[idx], term, for_csv    )
                l.append(term)

        return tuple(l)


    def get_result_dicts(self, sort_terms=(), offset=0, limit=0):
        return [self._tuple_to_dict(x) for x in self.get_result_tuples(sort_terms=sort_terms, offset=offset, limit=limit)]

class ResultWriteInterface(ResultInterface):
    def _setup_access(self):
        sql = "CREATE TABLE RESULT( %s );" % ", ".join([get_sqlite_term(x) for x in self.headers[1:]])
        self.cur.execute(sql)

        for x in self.headers:
            if x.get('index', ResultTableIndex.NONE) != ResultTableIndex.NONE:
                unique = "UNIQUE" if x['index'] == ResultTableIndex.UNIQUE else ""
                sql = "CREATE %s INDEX %s_idx on RESULT (%s)" % (unique, x['name'], x['name'])
                self.cur.execute(sql)

        fields = ", ".join(["'%s'" % x['name'] for x in self.headers[1:]])
        values = ", ".join([':%s' % x['name'] for x in self.headers[1:]])
        self.sql_insert = "INSERT INTO RESULT(%s) VALUES (%s);" % (fields, values)


    def add_result(self, info_dict):

        self.cur.execute(self.sql_insert, info_dict)
        return self.cur.lastrowid

    def flush(self):
        self.db.commit()

def create_result_writer(file_path, headers):
    return ResultWriteInterface(file_path, headers)

def create_result_reader(file_path, headers):
    return ResultReadInterface(file_path, headers)
