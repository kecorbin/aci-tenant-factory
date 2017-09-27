import json
from acitoolkit.acitoolkit import Tenant, Session

from flask import Flask, render_template, request, flash, redirect
app = Flask(__name__)

APIC = None
USERNAME = None
PASSWORD = None


def clone_tenant(session, existing, new):
    print "Creating new tenant {} using {} as a template".format(new, existing)
    url = '/api/node/class/fvTenant.json' \
          '?rsp-prop-include=config-only' \
          '&rsp-subtree=full' \
          '&query-target-filter=and(eq(fvTenant.name,"{}"))'.format(existing)
    source = session.get(url).json()['imdata'][0]
    new = json.dumps(source).replace(existing, new)
    return session.push_to_apic('/api/mo/uni.json', data=json.loads(new))


@app.route('/configure', endpoint='configure', methods=['GET', 'POST'])
def configure():
    global APIC, USERNAME, PASSWORD
    if request.method == 'GET':
        return render_template('configure.html')
    elif request.method == 'POST':
        try:
            APIC = request.form['apic']
            USERNAME = request.form['username']
            PASSWORD = request.form['password']
            flash('Successfully Updated Configuration', 'success')
            return redirect('/')
        except Exception as e:
            flash('Error: {}'.format(e), 'danger')


@app.route('/', endpoint='clone', methods=['GET', 'POST'])
def clone():
    if not all([USERNAME, PASSWORD, APIC]):
        flash('You must configure your environment before proceeding', 'warning')
        return redirect('/configure')
    else:
        session = Session('http://{}'.format(APIC), USERNAME, PASSWORD)
        print session.login()

    if request.method == 'GET':
        tenants = Tenant.get(session)
        print tenants[1].get_json()
        return render_template('index.html', tenants=tenants)

    elif request.method == 'POST':
        new_tenant = clone_tenant(session, request.form['srctenant'], request.form['newtenant'])
        if new_tenant.ok:
            flash("Successfully created tenant {}".format(request.form['newtenant']), 'success')
            tenants = Tenant.get(session)
            return render_template('index.html', tenants=tenants)


if __name__ == '__main__':
    app.secret_key = "CHANGE_ME"
    app.run(host='0.0.0.0', port=5000, debug=True)
