frappe.provide('hub');
frappe.provide('verp.hub');

verp.hub.cache = {};
hub.call = function call_hub_method(method, args={}, clear_cache_on_event) { // eslint-disable-line
	return new Promise((resolve, reject) => {

		// cache
		const key = method + JSON.stringify(args);
		if (verp.hub.cache[key]) {
			resolve(verp.hub.cache[key]);
		}

		// cache invalidation
		const clear_cache = () => delete verp.hub.cache[key];

		if (!clear_cache_on_event) {
			invalidate_after_5_mins(clear_cache);
		} else {
			verp.hub.on(clear_cache_on_event, () => {
				clear_cache(key);
			});
		}

		let res;
		if (hub.is_server) {
			res = frappe.call({
				method: 'hub.hub.api.' + method,
				args
			});
		} else {
			res = frappe.call({
				method: 'verp.hub_node.api.call_hub_method',
				args: {
					method,
					params: args
				}
			});
		}

		res.then(r => {
			if (r.message) {
				const response = r.message;
				if (response.error) {
					frappe.throw({
						title: __('Marketplace Error'),
						message: response.error
					});
				}

				verp.hub.cache[key] = response;
				verp.hub.trigger(`response:${key}`, { response });
				resolve(response);
			}
			reject(r);

		}).fail(reject);
	});
};

function invalidate_after_5_mins(clear_cache) {
	// cache invalidation after 5 minutes
	const timeout = 5 * 60 * 1000;

	setTimeout(() => {
		clear_cache();
	}, timeout);
}
