var React = require("react");
var JobStore = require("../stores/JobStore");

export var LoginCredentials = React.createClass({
    getInitialState: function() {
        return {username: '', password: ''};
    },
    usernameChanged: function(event) {
        this.setState({username: event.target.value});
    },
    passwordChanged: function(event) {
        this.setState({password: event.target.value});
    },
    render: function () {
        return (
            <form onSubmit={this.onSubmit} method="GET">
                <input type="text" placeholder="Username" onChange={this.usernameChanged}/>
                <input type="password" placeholder="Password"  onChange={this.passwordChanged}/>
                <input type="submit" className="btn btn-default btn-xs" value="Set" />
            </form>
        );
    },

    onSubmit: function(e) {
        e.preventDefault();
        JobStore.Actions.login(this.props.job.id, this.state.username, this.state.password);
    }
});