import { redirect } from "next/navigation"

type SearchParams = { [key: string]: string | string[] | undefined }

export default async function ReportIndexPage({
	searchParams,
}: {
	searchParams?: Promise<SearchParams>
}) {
	const resolvedParams = (await searchParams) ?? {}

	const params = new URLSearchParams()
	for (const [key, value] of Object.entries(resolvedParams)) {
		if (Array.isArray(value)) {
			for (const entry of value) {
				params.append(key, entry)
			}
		} else if (value) {
			params.set(key, value)
		}
	}

	const query = params.toString()
	const target = query ? `/report/overview?${query}` : "/report/overview"
	redirect(target)
}
